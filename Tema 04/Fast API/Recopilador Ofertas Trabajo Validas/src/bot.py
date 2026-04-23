import os
import asyncio
import requests
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

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
            f"🔗 <a href='{job_data.get('url')}'>Ver Oferta</a>"
        )

        # Create inline keyboard with CV generation button if offer_id is available
        keyboard = None
        offer_id = job_data.get('offer_id')
        if offer_id:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "📄 Generar CV Optimizado",
                    callback_data=f"gen_cv:{offer_id}"
                )]
            ])

        return self._send_message(message, keyboard)

    def _send_message(self, text: str, keyboard=None) -> bool:
        """Envía el payload final a la API de Telegram con teclado opcional."""
        try:
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": False
            }

            # Add inline keyboard if provided
            if keyboard:
                payload["reply_markup"] = keyboard.to_dict()

            response = requests.post(self.base_url, json=payload, timeout=10)
            response.raise_for_status() # Lanza error si no es 200 OK

            print("Notificación enviada a Telegram correctamente.")
            return True

        except requests.exceptions.RequestException as e:
            print(f"Error al enviar mensaje a Telegram: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Detalle API: {e.response.text}")
            return False

    async def handle_generate_cv_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the 'gen_cv:offer_id' callback query from inline button.

        Sends a NEW message for generation status instead of editing the original.
        This keeps the offer information intact regardless of success or error.
        """
        query = update.callback_query
        await query.answer()  # Remove loading spinner on button

        sent_message = None

        try:
            # Extract offer_id from callback_data (format: "gen_cv:123")
            offer_id = query.data.split(":")[1]

            # Send NEW message for processing status (don't edit original)
            sent_message = await query.message.reply_text(
                f"⏳ Generando CV optimizado para oferta #{offer_id}...",
                parse_mode="HTML"
            )

            # Call FastAPI endpoint to generate adapted CV
            base_url = os.getenv("API_BASE_URL", "http://localhost:7860")

            def make_cv_request():
                return requests.post(
                    f"{base_url}/api/generate/{offer_id}",
                    timeout=300
                )

            response = await asyncio.to_thread(make_cv_request)

            if response.status_code == 200:
                data = response.json()
                cv_url = data.get("adapted_cv_url")

                # Edit the status message with success and link
                await sent_message.edit_text(
                    f"✅ CV Optimizado Generado\n\n"
                    f"📎 <a href='{cv_url}'>Descargar PDF</a>",
                    parse_mode="HTML"
                )
            else:
                error_msg = response.json().get("detail", "Unknown error")
                # Escape error message to prevent HTML parsing issues
                error_msg_escaped = error_msg.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                await sent_message.edit_text(
                    f"❌ Error generando CV: {error_msg_escaped}",
                    parse_mode="HTML"
                )

        except IndexError:
            if sent_message:
                await sent_message.edit_text("❌ Datos inválidos en botón.", parse_mode="HTML")
            else:
                await query.message.reply_text("❌ Datos inválidos en botón.")
        except httpx.TimeoutException:
            if sent_message:
                await sent_message.edit_text("⏱️ Timeout: La compilación LaTeX tardó demasiado.", parse_mode="HTML")
            else:
                await query.message.reply_text("⏱️ Timeout: La compilación LaTeX tardó demasiado.")
        except Exception as e:
            print(f"[ERROR] Callback handler failed: {e}")
            error_text = str(e)[:100].replace("<", "&lt;").replace(">", "&gt;")
            if sent_message:
                try:
                    await sent_message.edit_text(f"❌ Error inesperado: {error_text}", parse_mode="HTML")
                except Exception as edit_err:
                    print(f"[WARN] Could not edit status message: {edit_err}")
                    await query.message.reply_text(f"❌ Error inesperado: {error_text}")
            else:
                await query.message.reply_text(f"❌ Error inesperado: {error_text}")

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