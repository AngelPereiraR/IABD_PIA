import os
import re
import base64
from typing import List
from dotenv import load_dotenv

from langchain_google_community import GmailToolkit

load_dotenv()

class GmailJobCollector:
    """
    Clase encargada de interactuar con la API de Gmail para buscar alertas nuevas
    y limpiar automáticamente TODO el historial antiguo de LinkedIn (>14 días).
    """
    def __init__(self):
        self.toolkit = GmailToolkit()
        self.service = self.toolkit.api_resource

    def get_linkedin_offers(self, limit: int = 5) -> List[str]:
        """
        Orquesta el proceso de limpieza y recolección.
        """
        # 1. Limpieza masiva (Ofertas antiguas + Spam/Notificaciones viejas)
        self._cleanup_old_emails()

        # 2. Busqueda de lo nuevo y relevante
        return self._fetch_recent_offers(limit)

    def _cleanup_old_emails(self):
        """
        Busca y elimina (mueve a papelera) CUALQUIER correo de LinkedIn
        que tenga más de 14 días (sean ofertas, notificaciones, mensajes, etc).
        Estrategia: 'from:linkedin older_than:14d'
        """
        # Query Simplificada: Todo lo que venga de LinkedIn y sea viejo se va.
        query = 'from:linkedin older_than:14d'
        
        try:
            page_token = None
            total_deleted = 0
            
            while True:
                # Pedimos página de resultados
                results = self.service.users().messages().list(
                    userId='me', 
                    q=query, 
                    maxResults=500, # Máximo permitido por página
                    pageToken=page_token
                ).execute()
                
                messages = results.get('messages', [])
                
                if messages:
                    batch_ids = [msg['id'] for msg in messages]
                    
                    # Borrado en bloque
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
                    print(f"   [LIMPIEZA] Lote procesado: {count} correos antiguos de LinkedIn movidos a papelera...")
                
                # Verificamos si hay más páginas
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            
            if total_deleted > 0:
                print(f"      [OK] Limpieza completada. Total eliminados: {total_deleted}")
            else:
                # Opcional: avisar que no había nada que limpiar
                pass
                
        except Exception as e:
            print(f"[ERROR] Error durante la limpieza automática: {e}")

    def _fetch_recent_offers(self, limit: int) -> List[str]:
        """
        Busca correos RECIENTES (<14 días) y NO LEÍDOS que sean ESPECÍFICAMENTE de ofertas.
        """
        found_urls = []
        # Usamos un set auxiliar para comprobación instantánea de duplicados
        seen_urls = set()
        
        # Query Específica: Solo queremos OFERTAS frescas, no mensajes de gente
        query = 'from:linkedin label:UNREAD newer_than:14d ("Ver empleos similares" OR "alertas de empleo" OR "publicado el" OR "principales empleos")'
        
        try:
            print(f"[BUSQUEDA] Buscando alertas recientes de empleo (<14 días)...")
            
            results = self.service.users().messages().list(
                userId='me', 
                q=query, 
                maxResults=limit
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                print("   [-] No hay alertas nuevas recientes.")
                return []

            print(f"   [+] Se encontraron {len(messages)} mensajes de alerta. Procesando...")

            for msg in messages:
                msg_id = msg['id']
                
                # Obtener contenido completo
                message_data = self.service.users().messages().get(
                    userId='me', id=msg_id, format='full'
                ).execute()
                
                # Extracción recursiva robusta
                body = self._get_message_body_recursive(message_data.get('payload', {}))
                
                # Regex IDs
                job_ids = re.findall(r'jobs/view/(\d+)', body)
                
                if job_ids:
                    new_urls_in_this_email = []
                    
                    for jid in job_ids:
                        full_url = f"https://www.linkedin.com/jobs/view/{jid}"
                        
                        # VERIFICACIÓN DE DUPLICADOS ANTES DE AÑADIR
                        if full_url not in seen_urls:
                            seen_urls.add(full_url)
                            new_urls_in_this_email.append(full_url)
                    
                    if new_urls_in_this_email:
                        found_urls.extend(new_urls_in_this_email)
                        print(f"     [+] {len(new_urls_in_this_email)} Oferta(s) NUEVA(S) extraída(s) del mensaje {msg_id}")
                    else:
                        print(f"     [.] Ofertas encontradas en mensaje {msg_id} pero ya eran duplicadas.")
                else:
                    print(f"     [-] No se detectaron IDs de oferta en mensaje {msg_id}")

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
        Busca recursivamente en las partes del mensaje (MIME multipart)
        hasta encontrar texto o HTML.
        """
        try:
            # Caso base: Si tiene cuerpo directo
            if 'body' in payload and payload['body'].get('data'):
                return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
            
            # Caso recursivo: Si tiene partes
            if 'parts' in payload:
                html_part = None
                text_part = None
                
                for part in payload['parts']:
                    mime_type = part.get('mimeType')
                    
                    # Prioridad 1: HTML
                    if mime_type == 'text/html':
                        html_part = part
                    # Prioridad 2: Texto plano
                    elif mime_type == 'text/plain':
                        text_part = part
                    # Prioridad 3: Contenedor anidado (multipart/alternative, related, etc)
                    elif mime_type and 'multipart' in mime_type:
                        # Llamada recursiva
                        return self._get_message_body_recursive(part)

                # Devolver lo mejor que encontramos en este nivel
                target_part = html_part or text_part
                if target_part:
                    return self._get_message_body_recursive(target_part)
                    
        except Exception:
            return ""
        return ""

if __name__ == "__main__":
    print("[TEST] Iniciando prueba del Agente de Correo (Limpieza TOTAL + Recientes)...")
    try:
        collector = GmailJobCollector()
        urls = collector.get_linkedin_offers(limit=5)
        print(f"\n--- RESULTADO: {len(urls)} URLs únicas extraídas ---")
        for u in urls:
            print(f" -> {u}")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")