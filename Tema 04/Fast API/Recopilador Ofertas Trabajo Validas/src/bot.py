import os
import requests
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

    def _send_message(self, text: str) -> bool:
        """Envía el payload final a la API de Telegram."""
        try:
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": False
            }

            response = requests.post(self.base_url, json=payload, timeout=10)
            response.raise_for_status()

            print("Notificación enviada a Telegram correctamente.")
            return True

        except requests.exceptions.RequestException as e:
            print(f"Error al enviar mensaje a Telegram: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Detalle API: {e.response.text}")
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