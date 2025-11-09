"""
Script para limpiar y normalizar documentos extraídos sobre TEA en Andalucía
Elimina ruido, unifica formato y mejora la legibilidad del contenido
"""

import re
from pathlib import Path
from typing import List, Set, Tuple
import logging
from collections import Counter
import unicodedata

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DocumentCleaner:
    """Limpiador de documentos extraídos"""
    
    def __init__(self, input_dir: str = "documentos_tea_andalucia"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(f"{input_dir}_limpio")
        self.output_dir.mkdir(exist_ok=True)
        
        # Estadísticas
        self.stats = {
            'procesados': 0,
            'errores': 0,
            'lineas_eliminadas': 0,
            'duplicados_eliminados': 0
        }
        
        # Patrones comunes de ruido
        self.noise_patterns = [
            # Números de página
            r'^Página\s+\d+\s*$',
            r'^\d+\s*$',
            r'^-\s*\d+\s*-\s*$',
            r'^\[\s*\d+\s*\]$',
            
            # Cabeceras y pies típicos
            r'^BOJA\s+núm\.\s+\d+',
            r'^Boletín Oficial de la Junta de Andalucía',
            r'^www\.juntadeandalucia\.es',
            r'^https?://[^\s]+$',
            r'^Depósito Legal:',
            r'^ISSN:',
            
            # Separadores y líneas vacías múltiples
            r'^[=\-_*]{3,}$',
            r'^\.{3,}$',
            
            # Fechas sueltas sin contexto
            r'^\d{1,2}/\d{1,2}/\d{4}$',
            
            # Menús de navegación web
            r'^(Inicio|Menú|Buscar|Contacto|Imprimir|Compartir)\s*$',
            r'^(Volver|Ir a|Ver más|Leer más)\s*$',
            
            # Cookies y avisos legales genéricos
            r'^Este sitio web utiliza cookies',
            r'^Política de privacidad',
            r'^Aviso legal',
            
            # Metadatos técnicos
            r'^Content-Type:',
            r'^Encoding:',
            
            # Texto de imagen/enlace roto
            r'^\[Imagen:.*\]$',
            r'^\[Link:.*\]$',
        ]
        
        # Patrones de cabeceras repetitivas
        self.header_keywords = [
            'consejería', 'junta de andalucía', 'boja', 'boe',
            'boletín oficial', 'depósito legal', 'issn', 'nipo'
        ]
    
    def is_noise_line(self, line: str) -> bool:
        """Determina si una línea es ruido"""
        line_stripped = line.strip()
        
        # Líneas vacías o muy cortas (menos de 3 caracteres)
        if len(line_stripped) < 3:
            return True
        
        # Líneas que solo contienen espacios, guiones, puntos, etc.
        if re.match(r'^[\s\-_.=*]+$', line_stripped):
            return True
        
        # Aplicar patrones de ruido
        for pattern in self.noise_patterns:
            if re.match(pattern, line_stripped, re.IGNORECASE):
                return True
        
        return False
    
    def detect_repeated_headers(self, lines: List[str], threshold: int = 3) -> Set[str]:
        """Detecta cabeceras que se repiten frecuentemente en el documento"""
        # Contar líneas que aparecen múltiples veces
        line_counts = Counter([line.strip() for line in lines if len(line.strip()) > 10])
        
        repeated = set()
        for line, count in line_counts.items():
            if count >= threshold:
                # Verificar si contiene palabras clave de cabecera
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in self.header_keywords):
                    repeated.add(line)
        
        return repeated
    
    def remove_consecutive_duplicates(self, lines: List[str]) -> List[str]:
        """Elimina líneas duplicadas consecutivas"""
        if not lines:
            return lines
        
        cleaned = [lines[0]]
        duplicates_removed = 0
        
        for i in range(1, len(lines)):
            current = lines[i].strip()
            previous = lines[i-1].strip()
            
            # Solo añadir si no es exactamente igual a la anterior
            if current != previous or len(current) == 0:
                cleaned.append(lines[i])
            else:
                duplicates_removed += 1
        
        self.stats['duplicados_eliminados'] += duplicates_removed
        return cleaned
    
    def normalize_whitespace(self, text: str) -> str:
        """Normaliza espacios en blanco y saltos de línea"""
        # Convertir múltiples espacios en uno solo
        text = re.sub(r' +', ' ', text)
        
        # Convertir múltiples saltos de línea en máximo dos (párrafo)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Eliminar espacios al inicio y final de cada línea
        lines = [line.strip() for line in text.split('\n')]
        
        return '\n'.join(lines)
    
    def normalize_encoding(self, text: str) -> str:
        """Normaliza la codificación del texto"""
        # Normalizar unicode (NFD -> NFC)
        text = unicodedata.normalize('NFC', text)
        
        # Corregir caracteres mal codificados comunes
        replacements = {
            'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú',
            'Ã±': 'ñ', 'Ã¼': 'ü', 'Ã': 'Á', 'Ã‰': 'É', 'Ã': 'Í',
            'Ã"': 'Ó', 'Ãš': 'Ú', 'Ã': 'Ñ', 'Â°': '°', 'Â«': '«',
            'Â»': '»', 'â€"': '—', 'â€"': '–', 'â€˜': ''', 'â€™': ''',
            'â€œ': '"', 'â€': '"', 'â€¢': '•', 'â‚¬': '€',
        }
        
        for wrong, correct in replacements.items():
            text = text.replace(wrong, correct)
        
        return text
    
    def clean_document_content(self, content: str) -> str:
        """Limpia el contenido de un documento"""
        lines = content.split('\n')
        
        # Detectar cabeceras repetidas
        repeated_headers = self.detect_repeated_headers(lines)
        
        cleaned_lines = []
        lines_removed = 0
        
        for line in lines:
            line_stripped = line.strip()
            
            # Saltar líneas de ruido
            if self.is_noise_line(line):
                lines_removed += 1
                continue
            
            # Saltar cabeceras repetidas
            if line_stripped in repeated_headers:
                lines_removed += 1
                continue
            
            cleaned_lines.append(line)
        
        self.stats['lineas_eliminadas'] += lines_removed
        
        # Eliminar duplicados consecutivos
        cleaned_lines = self.remove_consecutive_duplicates(cleaned_lines)
        
        # Reconstruir texto
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Normalizar espacios y codificación
        cleaned_text = self.normalize_whitespace(cleaned_text)
        cleaned_text = self.normalize_encoding(cleaned_text)
        
        return cleaned_text
    
    def extract_metadata(self, content: str) -> Tuple[dict, str]:
        """Extrae y preserva metadatos importantes del documento"""
        lines = content.split('\n')
        metadata = {}
        content_start = 0
        
        # Buscar sección de metadatos (primeras líneas del documento)
        in_metadata = False
        for i, line in enumerate(lines):
            if '=' * 20 in line:
                if not in_metadata:
                    in_metadata = True
                else:
                    content_start = i + 1
                    break
            elif in_metadata and ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    if key and value:
                        metadata[key] = value
        
        # Contenido sin metadatos
        main_content = '\n'.join(lines[content_start:])
        
        return metadata, main_content
    
    def rebuild_document(self, metadata: dict, content: str, original_path: Path) -> str:
        """Reconstruye el documento con formato limpio"""
        parts = []
        
        # Cabecera del documento
        parts.append("=" * 80)
        parts.append("DOCUMENTO LIMPIO Y NORMALIZADO")
        parts.append("=" * 80)
        parts.append("")
        
        # Metadatos esenciales
        if metadata:
            parts.append("INFORMACIÓN DEL DOCUMENTO:")
            parts.append("-" * 80)
            for key, value in metadata.items():
                if key in ['CATEGORÍA', 'TIPO', 'TÍTULO', 'URL ORIGINAL']:
                    parts.append(f"{key}: {value}")
            parts.append("")
        
        parts.append("=" * 80)
        parts.append("CONTENIDO:")
        parts.append("=" * 80)
        parts.append("")
        
        # Contenido limpio
        parts.append(content)
        
        # Pie de documento
        parts.append("")
        parts.append("=" * 80)
        parts.append(f"Documento original: {original_path.name}")
        parts.append("Procesado y limpiado automáticamente")
        parts.append("=" * 80)
        
        return '\n'.join(parts)
    
    def process_file(self, file_path: Path) -> bool:
        """Procesa un archivo individual"""
        try:
            logger.info(f"📄 Procesando: {file_path.name}")
            
            # Leer archivo con manejo de errores de encoding
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                logger.error(f"❌ No se pudo leer {file_path.name} con ninguna codificación")
                self.stats['errores'] += 1
                return False
            
            # Extraer metadatos
            metadata, main_content = self.extract_metadata(content)
            
            # Limpiar contenido
            cleaned_content = self.clean_document_content(main_content)
            
            # Reconstruir documento
            final_document = self.rebuild_document(metadata, cleaned_content, file_path)
            
            # Crear estructura de directorios en salida
            relative_path = file_path.relative_to(self.input_dir)
            output_path = self.output_dir / relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Guardar archivo limpio (siempre UTF-8)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_document)
            
            self.stats['procesados'] += 1
            logger.info(f"✅ Guardado: {output_path.relative_to(self.output_dir)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error procesando {file_path.name}: {e}")
            self.stats['errores'] += 1
            return False
    
    def process_directory(self, directory: Path = None) -> None:
        """Procesa todos los archivos .txt en un directorio recursivamente"""
        if directory is None:
            directory = self.input_dir
        
        # Buscar todos los archivos .txt
        txt_files = list(directory.rglob("*.txt"))
        
        logger.info(f"📂 Encontrados {len(txt_files)} archivos para procesar")
        logger.info(f"📁 Directorio de salida: {self.output_dir}")
        logger.info("")
        
        for file_path in txt_files:
            self.process_file(file_path)
    
    def generate_report(self) -> str:
        """Genera un reporte del proceso de limpieza"""
        report = []
        report.append("=" * 80)
        report.append("REPORTE DE LIMPIEZA DE DOCUMENTOS")
        report.append("=" * 80)
        report.append("")
        report.append(f"📊 ESTADÍSTICAS:")
        report.append(f"   • Archivos procesados correctamente: {self.stats['procesados']}")
        report.append(f"   • Archivos con errores: {self.stats['errores']}")
        report.append(f"   • Líneas de ruido eliminadas: {self.stats['lineas_eliminadas']}")
        report.append(f"   • Líneas duplicadas eliminadas: {self.stats['duplicados_eliminados']}")
        report.append("")
        report.append("✅ MEJORAS APLICADAS:")
        report.append("   • Eliminación de cabeceras y pies de página repetidos")
        report.append("   • Eliminación de números de página y separadores")
        report.append("   • Eliminación de texto duplicado consecutivo")
        report.append("   • Normalización de espacios en blanco")
        report.append("   • Unificación de codificación a UTF-8")
        report.append("   • Corrección de caracteres mal codificados")
        report.append("   • Preservación de metadatos importantes")
        report.append("")
        report.append(f"📁 Documentos limpios guardados en: {self.output_dir}")
        report.append("=" * 80)
        
        return '\n'.join(report)


def main():
    """Función principal"""
    
    print("=" * 80)
    print("🧹 LIMPIADOR DE DOCUMENTOS TEA ANDALUCÍA")
    print("=" * 80)
    print("\nEste script limpiará todos los documentos extraídos:")
    print("  • Elimina cabeceras, pies de página y ruido")
    print("  • Normaliza espacios y formato")
    print("  • Unifica codificación a UTF-8")
    print("  • Preserva contenido relevante y metadatos")
    print("\n" + "=" * 80 + "\n")
    
    # Crear limpiador
    cleaner = DocumentCleaner("documentos_tea_andalucia")
    
    # Procesar todos los documentos
    cleaner.process_directory()
    
    # Generar y guardar reporte
    report = cleaner.generate_report()
    
    report_path = cleaner.output_dir / "00_REPORTE_LIMPIEZA.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Mostrar reporte
    print("\n" + report)
    print(f"\n📋 Reporte guardado en: {report_path}")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()