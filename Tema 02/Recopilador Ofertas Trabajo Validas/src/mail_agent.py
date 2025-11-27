import os
import re
import base64
import requests # Necesario para resolver redirecciones
from typing import List
from dotenv import load_dotenv

from langchain_google_community import GmailToolkit

load_dotenv()

class GmailJobCollector:
    """
    Clase encargada de interactuar con la API de Gmail para buscar alertas nuevas
    y limpiar automáticamente TODO el historial antiguo (>14 días).
    Soporta: LinkedIn e InfoJobs (con resolución de tracking links).
    """
    def __init__(self):
        self.toolkit = GmailToolkit()
        self.service = self.toolkit.api_resource

    def get_offers(self, limit: int = 5) -> List[str]:
        """
        Orquesta el proceso de limpieza y recolección.
        """
        # 1. Limpieza masiva (Ofertas antiguas + Spam/Notificaciones viejas)
        self._cleanup_old_emails()

        # 2. Busqueda de lo nuevo y relevante
        return self._fetch_recent_offers(limit)

    def _cleanup_old_emails(self):
        """
        Busca y elimina correos antiguos de LinkedIn o InfoJobs (>14 días).
        """
        query = 'from:"linkedin OR infojobs" older_than:14d'
        
        try:
            page_token = None
            total_deleted = 0
            
            while True:
                results = self.service.users().messages().list(
                    userId='me', 
                    q=query, 
                    maxResults=500,
                    pageToken=page_token
                ).execute()
                
                messages = results.get('messages', [])
                
                if messages:
                    batch_ids = [msg['id'] for msg in messages]
                    
                    self.service.users().messages().batchModify(
                        userId='me',
                        body={
                            'ids': batch_ids,
                            'addLabelIds': ['TRASH'], 
                            'removeLabelIds': []
                        }
                    ).execute()
                    
                    count = len(messages)
                    total_deleted += count
                    print(f"   [LIMPIEZA] Lote procesado: {count} correos antiguos movidos a papelera...")
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            
            if total_deleted > 0:
                print(f"      [OK] Limpieza completada. Total eliminados: {total_deleted}")
                
        except Exception as e:
            print(f"[ERROR] Error durante la limpieza automática: {e}")

    def _fetch_recent_offers(self, limit: int) -> List[str]:
        """
        Busca correos RECIENTES (<14 días) y NO LEÍDOS.
        Distingue entre LinkedIn e InfoJobs para extraer las URLs correctamente.
        """
        found_urls = []
        seen_urls = set()
        
        # Query optimizada para ambos proveedores
        query = 'from:("linkedin" OR "infojobs") label:UNREAD newer_than:14d ("Ver empleos similares" OR "alertas de empleo" OR "publicado el" OR "principales empleos" OR "Alerta de empleo InfoJobs" OR "Nueva oferta de empleo")'
        
        try:
            print(f"[BUSQUEDA] Buscando alertas recientes (<14 días)...")
            
            results = self.service.users().messages().list(
                userId='me', 
                q=query, 
                maxResults=limit
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                print("   [-] No hay alertas nuevas recientes.")
                return []

            print(f"   [+] Se encontraron {len(messages)} mensajes. Procesando...")

            for msg in messages:
                msg_id = msg['id']
                
                # Obtener mensaje completo
                message_data = self.service.users().messages().get(
                    userId='me', id=msg_id, format='full'
                ).execute()
                
                # Identificar origen
                headers = message_data.get('payload', {}).get('headers', [])
                sender = next((h['value'] for h in headers if h['name'] == 'From'), '').lower()
                
                body = self._get_message_body_recursive(message_data.get('payload', {}))
                
                new_urls_in_this_email = []

                # --- ESTRATEGIA LINKEDIN ---
                if 'linkedin' in sender:
                    job_ids = re.findall(r'jobs/view/(\d+)', body)
                    for jid in job_ids:
                        full_url = f"https://www.linkedin.com/jobs/view/{jid}"
                        if full_url not in seen_urls:
                            seen_urls.add(full_url)
                            new_urls_in_this_email.append(full_url)

                # --- ESTRATEGIA INFOJOBS (TRACKING RESOLVER) ---
                elif 'infojobs' in sender:
                    print("     [INFOJOBS] Detectado correo de InfoJobs. Buscando enlaces...")
                    
                    # 1. Buscar enlaces directos (limpios) si los hay
                    # Regex actualizada: Captura la URL completa hasta el final del ID, ignorando query params.
                    # El patrón [^"\s<>\']+ captura la ruta (ciudad/puesto) y se detiene ante comillas o espacios.
                    # El final /of-[a-zA-Z0-9]+ asegura que es una oferta y se detiene antes de ? (ya que ? no es alfanumérico ni guión)
                    clean_matches = re.findall(r'https?://(?:www\.)?infojobs\.net/[^"\s<>\']+/of-[a-zA-Z0-9]+', body)
                    
                    for url in clean_matches:
                        # La URL capturada por regex ya debería estar limpia, pero aseguramos
                        clean_url = url
                        if clean_url not in seen_urls:
                            seen_urls.add(clean_url)
                            new_urls_in_this_email.append(clean_url)

                    # 2. Buscar enlaces de TRACKING (link.push.infojobs.net)
                    # El regex busca URLs que empiecen por el dominio de tracking hasta encontrar un espacio o comilla
                    tracking_matches = re.findall(r'https?://link\.push\.infojobs\.net/ls/click\?[^\s"\'<>]+', body)
                    
                    if tracking_matches:
                        print(f"     [INFOJOBS] Resolviendo {len(tracking_matches)} enlaces de seguimiento...")
                        
                        for t_url in tracking_matches:
                            try:
                                # Resolvemos la redirección sin descargar el contenido (stream=True)
                                response = requests.get(t_url, allow_redirects=True, timeout=5, stream=True)
                                final_url = response.url
                                response.close() # Cerramos conexión rápido
                                
                                # Verificamos si la URL final es una oferta válida (tiene 'of-XXXX')
                                if "/of-" in final_url:
                                    # Usamos la URL final real (con ciudad/titulo) pero quitamos los parámetros (?...)
                                    clean_url = final_url.split('?')[0]
                                    
                                    if clean_url not in seen_urls:
                                        seen_urls.add(clean_url)
                                        new_urls_in_this_email.append(clean_url)
                            except Exception as e:
                                # Si falla una redirección, seguimos con la siguiente
                                print(f"     [WARN] Fallo al resolver enlace InfoJobs: {e}")
                                pass

                # --- LOGGING Y MARCADO ---
                if new_urls_in_this_email:
                    found_urls.extend(new_urls_in_this_email)
                    provider = "LinkedIn" if "linkedin" in sender else "InfoJobs"
                    print(f"     [+] {len(new_urls_in_this_email)} Oferta(s) de {provider} extraída(s) en mensaje {msg_id}")
                
                # Marcar como leído
                self.service.users().messages().modify(
                    userId='me',
                    id=msg_id,
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()

        except Exception as e:
            print(f"[ERROR] Error al procesar correos recientes: {e}")
        
        return found_urls

    def _get_message_body_recursive(self, payload) -> str:
        """
        Busca recursivamente en las partes del mensaje (MIME multipart).
        """
        try:
            if 'body' in payload and payload['body'].get('data'):
                return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
            
            if 'parts' in payload:
                html_part = None
                text_part = None
                
                for part in payload['parts']:
                    mime_type = part.get('mimeType')
                    if mime_type == 'text/html':
                        html_part = part
                    elif mime_type == 'text/plain':
                        text_part = part
                    elif mime_type and 'multipart' in mime_type:
                        return self._get_message_body_recursive(part)

                target_part = html_part or text_part
                if target_part:
                    return self._get_message_body_recursive(target_part)
                    
        except Exception:
            return ""
        return ""

if __name__ == "__main__":
    print("[TEST] Iniciando prueba del Agente Multi-Plataforma...")
    try:
        collector = GmailJobCollector()
        urls = collector.get_offers(limit=2) 
        print(f"\n--- RESULTADO: {len(urls)} URLs únicas extraídas ---")
        for u in urls:
            print(f" -> {u}")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")