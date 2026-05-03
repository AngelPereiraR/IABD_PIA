import os
import time
import requests
import socket
from dotenv import load_dotenv
from uuid import UUID
from src.database import SessionLocal, TelegramNotification

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

    def send_match_alert(self, job_data: dict, analysis: dict, user_id: str = None, offer_id: int = None) -> bool:
        """
        Formatea y guarda alerta en BD para envío asíncrono (no bloquea).
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

        # Guardar en BD para procesamiento asíncrono
        return self._queue_telegram_message(message, user_id, offer_id)

    def _queue_telegram_message(self, message: str, user_id: str = None, offer_id: int = None) -> bool:
        """Guarda mensaje en BD para envío asíncrono (no bloquea)."""
        if not user_id or not offer_id:
            print("[TELEGRAM] ✗ user_id u offer_id faltantes. Mensaje NO encolado.")
            return False

        try:
            session = SessionLocal()
            notification = TelegramNotification(
                user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
                job_offer_id=offer_id,
                message=message,
                status="pending"
            )
            session.add(notification)
            session.commit()
            session.close()
            print(f"[TELEGRAM] ✓ Mensaje encolado en BD (ID: {notification.id})")
            return True
        except Exception as e:
            print(f"[TELEGRAM] ✗ Error encolando mensaje: {e}")
            if 'session' in locals():
                session.close()
            return False

    @staticmethod
    def send_queued_messages():
        """Worker: procesa mensajes pendientes. Llamado en background thread."""
        session = SessionLocal()
        try:
            # Obtener mensajes pendientes
            pending = session.query(TelegramNotification).filter(
                TelegramNotification.status == "pending"
            ).order_by(TelegramNotification.created_at).all()

            for notification in pending:
                TelegramNotifier._send_telegram_message(notification, session)

        except Exception as e:
            print(f"[TELEGRAM WORKER] Error procesando cola: {e}")
        finally:
            session.close()

    @staticmethod
    def _send_telegram_message(notification: TelegramNotification, session) -> bool:
        """Envía un mensaje individual a Telegram con reintentos."""
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        base_url = f"https://api.telegram.org/bot{token}/sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": notification.message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }

        try:
            response = requests.post(base_url, json=payload, timeout=20)
            response.raise_for_status()
            notification.status = "sent"
            session.commit()
            print(f"[TELEGRAM WORKER] ✓ Mensaje {notification.id} enviado correctamente")
            return True

        except requests.exceptions.RequestException as e:
            notification.retries += 1
            max_retries = 10
            if notification.retries >= max_retries:
                notification.status = "failed"
                print(f"[TELEGRAM WORKER] ✗ Mensaje {notification.id} falló después de {max_retries} intentos: {e}")
            else:
                # Mantener en pending para reintentar
                print(f"[TELEGRAM WORKER] ✗ Reintento {notification.retries}/{max_retries} para mensaje {notification.id}")
            session.commit()
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