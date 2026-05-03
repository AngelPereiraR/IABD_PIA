import os
import time
import requests
import socket
from dotenv import load_dotenv

load_dotenv()

class TelegramNotifier:
    """
    Gestiona el envío de notificaciones al usuario vía Telegram.
    Usa requests síncrono para evitar conflictos de event loops en el main.
    """
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.token or not self.chat_id:
            raise ValueError("Faltan credenciales de Telegram en el archivo .env")

        self.base_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def send_match_alert(self, job_data: dict, analysis: dict) -> bool:
        """
        Formatea y envía una alerta de trabajo encontrado con botón inline para generar CV.
        """
        # Extraemos datos
        score = analysis.get('score', 0)
        salary = analysis.get('salary', 'No especificado')
        posted = analysis.get('posted_date', 'Fecha no detectada')
        benefits = analysis.get('benefits', 'No especificados')

        # Lógica de Iconos
        if score >= 90:
            icon = "🔥"
            title = "CANDIDATO IDEAL"
        elif score >= 80:
            icon = "🚀"
            title = "CANDIDATO FUERTE"
        elif score >= 70:
            icon = "✅"
            title = "CANDIDATO APTO"
        else:
            icon = "⚠️"
            title = "MATCH DUDOSO"

        # Barra de progreso
        filled_blocks = int(score / 10)
        progress_bar = "🟩" * filled_blocks + "⬜" * (10 - filled_blocks)

        # Construcción del Mensaje Enriquecido
        message = (
            f"{icon} <b>{title} DETECTADO</b>\n"
            f"<b>Afinidad: {score}%</b>\n"
            f"{progress_bar}\n\n"
            f"💼 <b>Puesto:</b> {analysis.get('job_title', 'Puesto sin título')}\n"
            f"🏢 <b>Empresa:</b> {analysis.get('company', 'Empresa confidencial')}\n\n"
            f"💰 <b>Salario:</b> {salary}\n"
            f"🎁 <b>Beneficios:</b> {benefits}\n\n"
        )

        # Agregar skills si están disponibles
        key_skills = analysis.get('key_skills', [])
        if key_skills:
            skills_text = ", ".join(key_skills[:5])
            message += f"🔑 <b>Skills Clave:</b> {skills_text}\n\n"

        message += (
            f"📅 <b>Publicado:</b> {posted}\n\n"
            f"💡 <b>Análisis:</b>\n<i>{analysis.get('summary', 'Sin análisis detallado.')}</i>\n\n"
            f"🔗 <a href='{job_data.get('url')}'>Ver Oferta Completa</a>"
        )

        return self._send_message(message)

    def _diagnose_connection(self) -> None:
        """Diagnostica la conectividad a api.telegram.org"""
        print("\n[DIAG] Iniciando diagnóstico de conectividad a Telegram...")

        try:
            print("[DIAG] Resolviendo DNS para api.telegram.org...")
            ip = socket.gethostbyname("api.telegram.org")
            print(f"[DIAG] ✓ DNS resuelto: api.telegram.org → {ip}")
        except socket.gaierror as e:
            print(f"[DIAG] ✗ Error DNS: {e}")
            return

        try:
            print("[DIAG] Intentando conexión TCP a api.telegram.org:443...")
            sock = socket.create_connection(("api.telegram.org", 443), timeout=10)
            print(f"[DIAG] ✓ Conexión TCP establecida")
            sock.close()
        except (socket.timeout, socket.error) as e:
            print(f"[DIAG] ✗ Error conexión TCP: {e}")
            return

        try:
            print("[DIAG] Intentando petición HTTPS simple (HEAD)...")
            response = requests.head("https://api.telegram.org", timeout=10)
            print(f"[DIAG] ✓ HTTPS funciona. Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[DIAG] ✗ Error HTTPS: {type(e).__name__}: {e}")

    def _send_message(self, text: str, max_retries: int = 3) -> bool:
        """Envía el payload final a la API de Telegram con reintentos y logging detallado."""
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }

        for attempt in range(max_retries):
            try:
                print(f"\n[TELEGRAM] Intento {attempt + 1}/{max_retries}")
                print(f"[TELEGRAM] URL: {self.base_url[:50]}...")
                print(f"[TELEGRAM] Payload size: {len(str(payload))} bytes")
                print(f"[TELEGRAM] Timeout: 60s")

                response = requests.post(self.base_url, json=payload, timeout=60)
                response.raise_for_status()
                print(f"[TELEGRAM] ✓ Notificación enviada correctamente. Status: {response.status_code}")
                return True

            except requests.exceptions.ConnectTimeout:
                print(f"[TELEGRAM] ✗ ConnectTimeout (no se pudo conectar en 60s)")
                self._diagnose_connection()
                wait_time = 2 ** attempt
                if attempt < max_retries - 1:
                    print(f"[TELEGRAM] Reintentando en {wait_time}s...")
                    time.sleep(wait_time)

            except requests.exceptions.ReadTimeout:
                print(f"[TELEGRAM] ✗ ReadTimeout (respuesta tardó >60s)")
                wait_time = 2 ** attempt
                if attempt < max_retries - 1:
                    print(f"[TELEGRAM] Reintentando en {wait_time}s...")
                    time.sleep(wait_time)

            except requests.exceptions.ConnectionError as e:
                print(f"[TELEGRAM] ✗ ConnectionError: {e}")
                self._diagnose_connection()
                wait_time = 2 ** attempt
                if attempt < max_retries - 1:
                    print(f"[TELEGRAM] Reintentando en {wait_time}s...")
                    time.sleep(wait_time)

            except requests.exceptions.RequestException as e:
                print(f"[TELEGRAM] ✗ {type(e).__name__}: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"[TELEGRAM] Status: {e.response.status_code}")
                    print(f"[TELEGRAM] Response: {e.response.text[:200]}")
                wait_time = 2 ** attempt
                if attempt < max_retries - 1:
                    print(f"[TELEGRAM] Reintentando en {wait_time}s...")
                    time.sleep(wait_time)

        print("[TELEGRAM] ✗ Máximo de reintentos alcanzado. Mensaje NO enviado.")
        return False

if __name__ == "__main__":
    # --- PRUEBA UNITARIA ---
    print("Iniciando prueba de Notificación Telegram...")
    
    try:
        notifier = TelegramNotifier()
        
        # Datos simulados (Mock)
        fake_job = {"url": "https://www.linkedin.com/jobs/view/123456"}
        fake_analysis = {
            "match": True,
            "job_title": "Senior Python Developer",
            "company": "Tech Corp AI",
            "summary": "Buscan experto en LangChain y Python. Pagan bien y es remoto. Coincide con tu experiencia en APIs.",
            "match_score": 88.5,
            "salary": "50.000€ - 60.000€",
            "benefits": "Contrato indefinido, 100% remoto, seguro médico privado"
        }
        
        notifier.send_match_alert(fake_job, fake_analysis)
        
    except ValueError as e:
        print(f"\nConfiguración incompleta: {e}")