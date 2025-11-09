"""
Script para extraer información sobre trámites TEA en Andalucía
Extrae contenido de fuentes oficiales (HTML y PDF) y genera archivos individuales en texto plano
"""

import requests
from bs4 import BeautifulSoup
import PyPDF2
import re
from urllib.parse import urljoin, urlparse
from io import BytesIO
import time
from typing import List, Dict, Set
import logging
import os
from pathlib import Path
import unicodedata

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TEAInfoExtractor:
    """Extractor de información sobre TEA en Andalucía"""
    
    def __init__(self, output_dir: str = "documentos_tea_andalucia"):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.visited_urls: Set[str] = set()
        self.extracted_documents: List[Dict] = []
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Crear subdirectorios
        self.leyes_dir = self.output_dir / "01_leyes_y_normativa"
        self.procedimientos_dir = self.output_dir / "02_procedimientos_oficiales"
        self.guias_dir = self.output_dir / "03_guias_y_recursos"
        self.asociaciones_dir = self.output_dir / "04_asociaciones"
        
        for dir_path in [self.leyes_dir, self.procedimientos_dir, self.guias_dir, self.asociaciones_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def sanitize_filename(self, text: str, max_length: int = 150) -> str:
        """Limpia un texto para usarlo como nombre de archivo"""
        # Eliminar caracteres no válidos
        text = re.sub(r'[<>:"/\\|?*]', '', text)
        # Normalizar unicode
        text = unicodedata.normalize('NFKD', text)
        # Eliminar acentos
        text = text.encode('ASCII', 'ignore').decode('ASCII')
        # Reemplazar espacios y caracteres especiales
        text = re.sub(r'[\s\-]+', '_', text)
        # Eliminar puntos y comas
        text = text.replace('.', '').replace(',', '')
        # Limitar longitud
        if len(text) > max_length:
            text = text[:max_length]
        # Eliminar guiones bajos al inicio y final
        text = text.strip('_')
        return text if text else "documento"
    
    def classify_document(self, url: str, title: str) -> tuple:
        """Clasifica un documento y devuelve (directorio, categoría)"""
        url_lower = url.lower()
        title_lower = title.lower()
        
        # Leyes y normativa (BOJA y BOE)
        if any(kw in url_lower or kw in title_lower for kw in 
               ['boja', 'boe', 'ley', 'decreto', 'orden', 'resolucion', 'instruccion', 'real decreto', 'disposicion']):
            return self.leyes_dir, "LEY"
        
        # Procedimientos oficiales
        if any(kw in url_lower or kw in title_lower for kw in 
               ['tramite', 'procedimiento', 'solicitud', 'reconocimiento', 'valoracion']):
            return self.procedimientos_dir, "PROCEDIMIENTO"
        
        # Asociaciones
        if any(kw in url_lower for kw in ['autismo', 'mirame.org', 'asociacion']):
            return self.asociaciones_dir, "ASOCIACION"
        
        # Por defecto, guías y recursos
        return self.guias_dir, "GUIA"
    
    def is_relevant_link(self, url: str, text: str = "") -> bool:
        """Determina si un enlace es relevante para extraer"""
        url_lower = url.lower()
        text_lower = text.lower()
        
        # PRIORIDAD MÁXIMA: BOJA, BOE, leyes, decretos, normativa
        high_priority_keywords = [
            'boja', 'boe', 'ley', 'decreto', 'orden', 'resolucion', 'normativa',
            'legislacion', 'real decreto', 'instruccion', 'convenio', 'disposicion'
        ]
        
        for keyword in high_priority_keywords:
            if keyword in url_lower or keyword in text_lower:
                return True
        
        # Siempre incluir páginas del BOJA y BOE
        if any(domain in url_lower for domain in ['boja', 'juntadeandalucia.es/boja', 'boe.es']):
            return True
        
        # Incluir todos los PDFs (pueden ser leyes, guías, etc.)
        if url_lower.endswith('.pdf'):
            return True
        
        # Keywords secundarios (temas específicos)
        relevant_keywords = [
            'tea', 'autismo', 'discapacidad', 'dependencia', 'neae',
            'ayuda', 'prestacion', 'beca', 'atencion', 'temprana',
            'educativ', 'familia', 'guia', 'tramite', 'faq', 'pregunta',
            'infantil', 'especial', 'valoracion', 'orientacion'
        ]
        
        for keyword in relevant_keywords:
            if keyword in url_lower or keyword in text_lower:
                return True
        
        # Incluir páginas de la Junta de Andalucía y BOE
        if any(domain in url_lower for domain in ['juntadeandalucia', 'boe.es']):
            return True
            
        return False
    
    def extract_pdf_content(self, url: str) -> str:
        """Extrae texto de un PDF"""
        try:
            logger.info(f"📄 Extrayendo PDF: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            pdf_file = BytesIO(response.content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_content = []
            text_content.append(f"DOCUMENTO PDF")
            text_content.append(f"URL: {url}")
            text_content.append(f"Total de páginas: {len(pdf_reader.pages)}")
            text_content.append("=" * 80)
            text_content.append("")
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                if text.strip():
                    text_content.append(f"\n{'=' * 80}")
                    text_content.append(f"PÁGINA {page_num}")
                    text_content.append("=" * 80)
                    text_content.append(text)
            
            return "\n".join(text_content)
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo PDF {url}: {e}")
            return f"ERROR: No se pudo extraer el contenido del PDF\nURL: {url}\nError: {e}"
    
    def extract_html_content(self, url: str, extract_links: bool = True) -> Dict:
        """Extrae contenido de una página HTML"""
        try:
            logger.info(f"🌐 Extrayendo HTML: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Detectar encoding correcto
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Eliminar scripts, estilos y navegación
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()
            
            result = {
                'url': url,
                'title': '',
                'content': '',
                'pdf_links': [],
                'relevant_links': [],
                'metadata': {}
            }
            
            # Extraer título
            title_tag = soup.find('title')
            if title_tag:
                result['title'] = title_tag.get_text().strip()
            
            # Detectar si es página del BOJA o BOE (formato especial)
            is_boja = 'boja' in url.lower()
            is_boe = 'boe.es' in url.lower()
            
            # Extraer metadatos importantes (especialmente para BOJA, BOE y leyes)
            for meta in soup.find_all('meta'):
                name = meta.get('name', '').lower()
                content = meta.get('content', '')
                if name in ['description', 'keywords', 'dc.title', 'dc.subject', 'author']:
                    result['metadata'][name] = content
            
            # Extraer contenido principal
            if is_boja or is_boe:
                # Para BOJA y BOE, extraer TODO el contenido visible
                content_area = soup.body
            else:
                main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile('content|main|texto'))
                content_area = main_content if main_content else soup.body
            
            if content_area:
                text_parts = []
                
                # Extraer TODO el contenido textual relevante preservando estructura
                for tag in content_area.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'td', 'th', 'div', 'span', 'strong', 'em', 'article', 'section']):
                    text = tag.get_text(separator=' ', strip=True)
                    # Reducir requisito mínimo de caracteres para capturar artículos de leyes
                    if text and len(text) > 3:
                        # Evitar duplicados consecutivos
                        if not text_parts or text != text_parts[-1]:
                            text_parts.append(text)
                
                result['content'] = "\n\n".join(text_parts)
            
            # Extraer enlaces relevantes si se solicita
            if extract_links:
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    link_text = link.get_text().strip()
                    absolute_url = urljoin(url, href)
                    
                    # Clasificar enlaces
                    if absolute_url.lower().endswith('.pdf'):
                        if self.is_relevant_link(absolute_url, link_text):
                            result['pdf_links'].append({
                                'url': absolute_url,
                                'text': link_text or 'Documento PDF'
                            })
                    elif self.is_relevant_link(absolute_url, link_text):
                        # Evitar enlaces circulares
                        if absolute_url not in self.visited_urls:
                            result['relevant_links'].append({
                                'url': absolute_url,
                                'text': link_text or 'Enlace relacionado'
                            })
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo HTML {url}: {e}")
            return {
                'url': url,
                'title': '',
                'content': f"ERROR: No se pudo extraer el contenido\nURL: {url}\nError: {e}",
                'pdf_links': [],
                'relevant_links': [],
                'metadata': {}
            }
    
    def save_document(self, content: str, title: str, url: str, doc_type: str) -> str:
        """Guarda un documento individual en texto plano"""
        try:
            # Clasificar documento
            directory, category = self.classify_document(url, title)
            
            # Generar nombre de archivo único
            base_name = self.sanitize_filename(title)
            if not base_name or base_name == "documento":
                # Usar parte de la URL si no hay título
                parsed_url = urlparse(url)
                base_name = self.sanitize_filename(parsed_url.path.split('/')[-1])
            
            # Agregar contador si ya existe
            counter = 1
            file_name = f"{base_name}.txt"
            file_path = directory / file_name
            
            while file_path.exists():
                file_name = f"{base_name}_{counter}.txt"
                file_path = directory / file_name
                counter += 1
            
            # Preparar contenido del archivo
            file_content = []
            file_content.append("=" * 80)
            file_content.append(f"CATEGORÍA: {category}")
            file_content.append(f"TIPO: {doc_type}")
            file_content.append(f"TÍTULO: {title}")
            file_content.append(f"URL ORIGINAL: {url}")
            file_content.append("=" * 80)
            file_content.append("")
            file_content.append(content)
            
            # Guardar archivo
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(file_content))
            
            logger.info(f"💾 Guardado: {file_path.relative_to(self.output_dir)}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"❌ Error guardando documento {title}: {e}")
            return None
    
    def process_url(self, url: str, depth: int = 0, max_depth: int = 2) -> None:
        """Procesa una URL y sus enlaces relacionados recursivamente"""
        
        if url in self.visited_urls or depth > max_depth:
            return
        
        self.visited_urls.add(url)
        
        # Pausa para no saturar el servidor
        time.sleep(1)
        
        # Determinar tipo de documento
        is_boja = 'boja' in url.lower()
        is_boe = 'boe.es' in url.lower()
        is_legislative = any(kw in url.lower() for kw in ['ley', 'decreto', 'orden', 'resolucion'])
        
        if url.lower().endswith('.pdf'):
            # Procesar PDF
            content = self.extract_pdf_content(url)
            title = url.split('/')[-1].replace('.pdf', '')
            
            # Guardar documento individual
            file_path = self.save_document(content, title, url, 'PDF')
            
            if file_path:
                self.extracted_documents.append({
                    'type': 'PDF',
                    'url': url,
                    'title': title,
                    'file_path': file_path,
                    'priority': 'ALTA' if (is_boja or is_boe or is_legislative) else 'MEDIA'
                })
        else:
            # Procesar HTML
            result = self.extract_html_content(url, extract_links=(depth < max_depth))
            
            if result['content']:
                # Preparar contenido completo con metadatos
                full_content = []
                
                if result['metadata']:
                    full_content.append("METADATOS:")
                    full_content.append("-" * 80)
                    for key, value in result['metadata'].items():
                        if value:
                            full_content.append(f"{key.upper()}: {value}")
                    full_content.append("")
                    full_content.append("=" * 80)
                    full_content.append("CONTENIDO:")
                    full_content.append("=" * 80)
                    full_content.append("")
                
                full_content.append(result['content'])
                
                # Guardar documento individual
                file_path = self.save_document(
                    "\n".join(full_content),
                    result['title'],
                    result['url'],
                    'HTML'
                )
                
                if file_path:
                    self.extracted_documents.append({
                        'type': 'HTML',
                        'url': result['url'],
                        'title': result['title'],
                        'file_path': file_path,
                        'priority': 'ALTA' if (is_boja or is_boe or is_legislative) else 'MEDIA'
                    })
            
            # PRIORIDAD: Procesar TODOS los PDFs encontrados
            pdf_limit = 20 if (is_boja or is_boe or is_legislative) else 5
            for pdf_link in result['pdf_links'][:pdf_limit]:
                if pdf_link['url'] not in self.visited_urls:
                    logger.info(f"📄 PDF encontrado: {pdf_link['text']}")
                    self.process_url(pdf_link['url'], depth=depth, max_depth=max_depth)
            
            # Procesar enlaces HTML relevantes
            if depth < max_depth:
                link_limit = 10 if (is_boja or is_boe or is_legislative) else 3
                for link in result['relevant_links'][:link_limit]:
                    logger.info(f"🔗 Enlace relevante: {link['text']}")
                    self.process_url(link['url'], depth=depth + 1, max_depth=max_depth)
    
    def extract_from_sources(self, urls: List[str]) -> Dict:
        """Extrae información de una lista de URLs"""
        
        logger.info(f"Iniciando extracción de {len(urls)} fuentes...")
        logger.info("PRIORIDAD: Leyes, BOJA, decretos y normativa oficial")
        
        for url in urls:
            try:
                # Mayor profundidad para páginas legislativas
                is_legislative = any(kw in url.lower() for kw in ['boja', 'ley', 'decreto', 'orden'])
                depth = 2 if is_legislative else 1
                self.process_url(url, depth=0, max_depth=depth)
            except Exception as e:
                logger.error(f"Error procesando {url}: {e}")
        
        # Generar resumen
        return self.generate_summary()
    
    def generate_summary(self) -> Dict:
        """Genera un resumen de la extracción"""
        
        summary = {
            'total_documentos': len(self.extracted_documents),
            'total_urls': len(self.visited_urls),
            'por_tipo': {},
            'por_prioridad': {},
            'por_categoria': {}
        }
        
        # Contar por tipo
        for doc in self.extracted_documents:
            doc_type = doc['type']
            summary['por_tipo'][doc_type] = summary['por_tipo'].get(doc_type, 0) + 1
        
        # Contar por prioridad
        for doc in self.extracted_documents:
            priority = doc['priority']
            summary['por_prioridad'][priority] = summary['por_prioridad'].get(priority, 0) + 1
        
        # Contar por categoría (directorio)
        for doc in self.extracted_documents:
            file_path = Path(doc['file_path'])
            category = file_path.parent.name
            summary['por_categoria'][category] = summary['por_categoria'].get(category, 0) + 1
        
        return summary
    
    def save_index(self):
        """Guarda un índice de todos los documentos extraídos"""
        index_path = self.output_dir / "00_INDICE_DOCUMENTOS.txt"
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("ÍNDICE DE DOCUMENTOS EXTRAÍDOS - TEA ANDALUCÍA\n")
            f.write("=" * 80 + "\n\n")
            
            # Agrupar por directorio
            by_directory = {}
            for doc in self.extracted_documents:
                file_path = Path(doc['file_path'])
                dir_name = file_path.parent.name
                if dir_name not in by_directory:
                    by_directory[dir_name] = []
                by_directory[dir_name].append(doc)
            
            # Escribir por categoría
            for dir_name in sorted(by_directory.keys()):
                f.write(f"\n{'=' * 80}\n")
                f.write(f"{dir_name.upper()}\n")
                f.write("=" * 80 + "\n\n")
                
                for idx, doc in enumerate(by_directory[dir_name], 1):
                    file_path = Path(doc['file_path'])
                    f.write(f"[{idx}] {doc['title']}\n")
                    f.write(f"    Archivo: {file_path.name}\n")
                    f.write(f"    Tipo: {doc['type']}\n")
                    f.write(f"    Prioridad: {doc['priority']}\n")
                    f.write(f"    URL: {doc['url']}\n")
                    f.write("\n")
        
        logger.info(f"📋 Índice guardado: {index_path}")


def main():
    """Función principal"""
    
    # URLs del documento proporcionado (ordenadas por prioridad)
    urls_fuentes = [
        # ===== MÁXIMA PRIORIDAD: LEYES Y NORMATIVA (BOJA) =====
        "https://www.juntadeandalucia.es/boja/2023/36/1",  # Ley 1/2023 Atención Infantil Temprana
        "https://www.rpdiscapacidad.gob.es/docs/Res_TEA.pdf",  # Ley 4/2017 Derechos Discapacidad
        "https://www.juntadeandalucia.es/organismos/desarrolloeducativoyformacionprofesional/areas/centros-educativos/atencion-diversidad.html",  # Decreto 147/2002
        
        # ===== ALTA PRIORIDAD: PROCEDIMIENTOS OFICIALES =====
        "https://www.juntadeandalucia.es/servicios/sede/tramites/procedimientos/detalle/69.html",  # Discapacidad
        "https://www.juntadeandalucia.es/organismos/inclusionsocialjuventudfamiliaseigualdad/areas/dependencia/solicitud.html",  # Dependencia
        "https://www.juntadeandalucia.es/servicios/sede/ventanillas/dependencia.html",  # VED
        
        # ===== CENTROS Y VALORACIÓN =====
        "https://www.juntadeandalucia.es/organismos/inclusionsocialjuventudfamiliaseigualdad/areas/discapacidad/cvo.html",  # CVO
        "https://www.juntadeandalucia.es/organismos/saludyconsumo/areas/salud-vida/adulta/paginas/ive-discapacidad.html",  # CAIT
        
        # ===== EDUCACIÓN Y NEAE =====
        "https://www.juntadeandalucia.es/educacion/portals/web/escuela-familias/necesidades-especificas-de-apoyo-educativo/necesidades-educativas-especiales/trastornos-del-espectro-autista",
        "https://www.juntadeandalucia.es/educacion/portals/web/familias",
        "https://www.educacionfpydeportes.gob.es/servicios-al-ciudadano/catalogo/general/05/050140/ficha/050140-2024.html",  # Becas NEE
        
        # ===== PRESTACIONES =====
        "https://www.juntadeandalucia.es/temas/familias-igualdad/discapacidad/prestaciones.html",
        "https://www.seg-social.es/wps/portal/wss/internet/Trabajadores/PrestacionesPensionesTrabajadores/61fce0cb-bb6d-4bfa-8e83-61ec6e2bce86",
        
        # ===== ATENCIÓN TEMPRANA Y FAMILIAS =====
        "https://www.familiasandalucia.es/familias-con-necesidades-especiales/",
        
        # ===== GUÍAS Y RECURSOS (PDFs) =====
        "https://www.mirame.org/main/wp-content/uploads/2022/01/prestaciones-servicios-TEA.pdf",
        "https://andaluciainforma.eldiario.es/tramites/como-solicitar-de-forma-correcta-el-reconocimiento-del-grado-de-discapacidad-en-andalucia/",
        "https://www.unir.net/educacion/revista/noticias/como-solicitar-ley-dependencia-andalucia/",
        
        # ===== ASOCIACIONES =====
        "https://www.autismoandalucia.org/autismo/servicios-y-recursos/",
        "https://www.autismoandalucia.org/entradas-autismo/comunicado-sobre-el-convenio-de-apoyo-al-alumnado-con-tea/",
        "https://www.autismosevilla.org/apoyos-individualizados.php",
        "https://www.autismosevilla.org/blog/programas-de-apoyo-para-familiares-cuidadores-de-personas-con-tea/",
        
        # ===== INFORMACIÓN ADICIONAL =====
        "https://www.defensordelpuebloandaluz.es/reclamamos-que-se-potencie-y-extienda-la-disponibilidad-de-aulas-especificas-de-atencion-al-alumnado",
        "https://educaorientamalaga.com/ayudas-y-becas-para-alumnado-con-necesidades-educativas-en-andalucia/",
        "https://criando247.com/andalucia-ayuda-autonomia-discapacidad/",
    ]
    
    # Crear extractor y procesar
    extractor = TEAInfoExtractor()
    
    print("=" * 80)
    print("🔍 EXTRACTOR DE INFORMACIÓN TEA ANDALUCÍA")
    print("   Cada documento se guardará en un archivo individual")
    print("=" * 80)
    print(f"\n📋 Se procesarán {len(urls_fuentes)} fuentes principales")
    print("⚡ PRIORIDAD: Leyes, BOJA, decretos y normativa oficial")
    print(f"\n📁 Directorio de salida: {extractor.output_dir.absolute()}")
    print("\n⏳ Este proceso puede tardar varios minutos...")
    print("   - Se extraerán leyes completas del BOJA")
    print("   - Se seguirán enlaces a normativa relacionada")
    print("   - Se descargarán todos los PDFs relevantes")
    print("   - Cada documento se guardará en un archivo .txt separado")
    print("\n" + "=" * 80 + "\n")
    
    summary = extractor.extract_from_sources(urls_fuentes)
    
    # Guardar índice
    extractor.save_index()
    
    print("\n" + "=" * 80)
    print("✅ EXTRACCIÓN COMPLETADA")
    print("=" * 80)
    print(f"📁 Directorio: {extractor.output_dir.absolute()}")
    print(f"\n📊 ESTADÍSTICAS:")
    print(f"   • Total de documentos extraídos: {summary['total_documentos']}")
    print(f"   • Total de URLs visitadas: {summary['total_urls']}")
    print(f"\n📄 Por tipo:")
    for doc_type, count in summary['por_tipo'].items():
        print(f"   • {doc_type}: {count}")
    print(f"\n⚡ Por prioridad:")
    for priority, count in summary['por_prioridad'].items():
        print(f"   • {priority}: {count}")
    print(f"\n📂 Por categoría:")
    for category, count in summary['por_categoria'].items():
        print(f"   • {category}: {count}")
    print("\n" + "=" * 80)
    print(f"📋 Consulta el índice completo en: 00_INDICE_DOCUMENTOS.txt")
    print("=" * 80)


if __name__ == "__main__":
    main()