import os
import re
import base64
from typing import List
from dotenv import load_dotenv

# Reutilizamos la lógica de autenticación de LangChain que ya tienes configurada
from langchain_google_community import GmailToolkit

load_dotenv()

class GmailJobCollector:
    """
    Clase encargada de interactuar con la API de Gmail para buscar, 
    parsear y limpiar alertas de trabajo de LinkedIn.
    """
    def __init__(self):
        # Inicializamos el toolkit igual que en tu script original.
        # Esto buscará 'credentials.json' y 'token.json' automáticamente.
        self.toolkit = GmailToolkit()
        self.service = self.toolkit.api_resource  # Acceso directo al servicio de Google API

    def get_linkedin_offers(self, limit: int = 5) -> List[str]:
        """
        Busca correos no leídos de LinkedIn Job Alerts, extrae las URLs
        de las ofertas y marca los correos como leídos.

        Args:
            limit (int): Número máximo de correos a procesar por ciclo.

        Returns:
            List[str]: Lista de URLs de ofertas encontradas.
        """
        found_urls = []
        
        # 1. Búsqueda eficiente usando sintaxis de Gmail
        # from:linkedin busca correos de LinkedIn
        # "job alert" asegura que sea una alerta de empleo
        # label:UNREAD solo trae los nuevos
        query = 'from:linkedin label:UNREAD ("Ver empleos similares" OR "alertas de empleo" OR "publicado el" OR "principales empleos")'
        
        try:
            print(f"📧 Buscando alertas de LinkedIn nuevas (Query: '{query}')...")
            
            # Llamada directa a la API de Gmail (más rápido que un Agente LLM)
            results = self.service.users().messages().list(
                userId='me', 
                q=query, 
                maxResults=limit
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                print("   ✓ No hay alertas nuevas.")
                return []

            print(f"   ✓ Se encontraron {len(messages)} alertas. Procesando...")

            for msg in messages:
                msg_id = msg['id']
                
                # 2. Obtener el contenido del mensaje
                message_data = self.service.users().messages().get(
                    userId='me', 
                    id=msg_id, 
                    format='full'
                ).execute()
                
                # Extraer cuerpo del correo (HTML o Texto)
                body = self._get_message_body(message_data)
                
                # 3. Extraer URL con Regex (CORREGIDO PARA MULTIPLES OFERTAS)
                # Usamos findall en lugar de search para obtener TODAS las coincidencias
                urls_in_email = re.findall(r'https://www\.linkedin\.com/(?:comm/)?jobs/view/\d+', body)
                
                if urls_in_email:
                    # Eliminamos duplicados dentro del mismo correo (a veces el link sale 2 veces)
                    unique_msg_urls = list(set(urls_in_email))
                    found_urls.extend(unique_msg_urls)
                    print(f"     + {len(unique_msg_urls)} Oferta(s) detectada(s) en mensaje {msg_id}")
                else:
                    print(f"     - No se encontró URL válida en el mensaje {msg_id}")

                # 4. Marcar como leído (Quitar etiqueta UNREAD)
                self.service.users().messages().modify(
                    userId='me',
                    id=msg_id,
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()

        except Exception as e:
            print(f"❌ Error al procesar correos: {e}")
        
        return found_urls

    def _get_message_body(self, message_data) -> str:
        """Decodifica el cuerpo del mensaje buscando partes HTML o Texto plano."""
        try:
            payload = message_data.get('payload', {})
            parts = payload.get('parts', [])
            body_data = None

            # Estrategia: Buscar primero HTML, luego Texto plano
            if not parts:
                # Si no tiene partes (es un mensaje simple)
                body_data = payload.get('body', {}).get('data')
            else:
                for part in parts:
                    if part['mimeType'] == 'text/html':
                        body_data = part['body'].get('data')
                        break
                
                if not body_data:
                    # Fallback a texto plano si no hay HTML
                    for part in parts:
                        if part['mimeType'] == 'text/plain':
                            body_data = part['body'].get('data')
                            break

            if body_data:
                # Decodificar Base64URL
                return base64.urlsafe_b64decode(body_data).decode('utf-8')
            
        except Exception:
            return ""
        return ""

if __name__ == "__main__":
    # --- PRUEBA UNITARIA ---
    print("🧪 Iniciando prueba del Agente de Correo...")
    
    # Asegúrate de tener 'credentials.json' en la raíz (donde ejecutas el script)
    # y de haber corrido 'gmail_tool.py' al menos una vez para generar 'token.json'
    try:
        collector = GmailJobCollector()
        urls = collector.get_linkedin_offers(limit=1)
        
        print("\n--- RESULTADO DE LA PRUEBA ---")
        print(f"Ofertas extraídas: {len(urls)}")
        for i, url in enumerate(urls, 1):
            print(f"{i}. {url}")
            
    except Exception as e:
        print(f"\n🛑 Error: {e}")
        print("💡 PISTA: Verifica que 'credentials.json' esté en la carpeta raíz.")