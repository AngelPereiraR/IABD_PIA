import os
from dotenv import load_dotenv
load_dotenv()

from typing import List, Optional # Importamos tipos necesarios
from langchain_google_community import GmailToolkit
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from pydantic import BaseModel, Field

# Schema para enviar y/o crear borradores de correo
class GmailSendMessageSchema(BaseModel):
    """Schema for sending or drafting emails."""
    message: str = Field(..., description="The message to send.")
    # IMPORTANTE: Cambiado a list[str]
    to: list[str] = Field(..., description="The list of recipients (e.g. ['email@example.com']).")
    subject: str = Field(..., description="The subject of the email.")
    # IMPORTANTE: Cambiado a list[str] y opcional
    cc: Optional[list[str]] = Field(None, description="The list of cc recipients.")
    bcc: Optional[list[str]] = Field(None, description="The list of bcc recipients.")

# Función auxiliar para extraer texto limpio
def imprimir_respuesta_limpia(response_dict):
    if response_dict and "messages" in response_dict:
        last_message = response_dict["messages"][-1]
        content = last_message.content

        if isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
            print(f"Respuesta: {''.join(text_parts)}")
        else:
            print(f"Respuesta: {content}")
    else:
        print(f"Respuesta completa (debug): {response_dict}")


# 1. Configura tu llave de Google
print("🔑 Configurando la llave de Google...")
os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

# 2. Inicialización del Toolkit de Gmail
print("📧 Inicializando el Toolkit de Gmail...")
toolkit = GmailToolkit()

# 3. Obtener las herramientas
print("⚙️ Obteniendo herramientas del Toolkit de Gmail...")
tools = toolkit.get_tools()

# 4. Configurar el LLM
print("🧠 Configurando el LLM...")
llm = ChatGoogleGenerativeAI(temperature=0, model="gemini-2.5-flash")

# 5. Crear el Agente
print("🤖 Creando el agente (LangGraph)...")
system_prompt = "You are a helpful assistant that manages Gmail. Use the available tools to read, search, and send emails."

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt
)

print("🚀 Agente listo para interactuar con Gmail!")

for tool in tools:
    if tool.name in ["create_gmail_draft", "send_gmail_message"]:
        tool.args_schema = GmailSendMessageSchema
        print(f"✅ Patched schema for {tool.name}")

# --- USO EN TUS EJEMPLOS ---

print("--- EJEMPLO 1: Leer correos ---")
query_lectura = "Busca el último correo que recibí de 'notifications@github.com' y resume su contenido."
try:
    response = agent.invoke({"messages": [{"role": "user", "content": query_lectura}]})
    imprimir_respuesta_limpia(response)
except Exception as e:
    print(f"Error en lectura: {e}")

print("\n--- EJEMPLO 2: Crear un borrador ---")
query_escritura = "Crea un borrador de respuesta para el destinatario 'ampr2003@gmail.com' agradeciendo la información. Firma como 'Tu Asistente AI'."

try:
    response = agent.invoke({"messages": [{"role": "user", "content": query_escritura}]})
    imprimir_respuesta_limpia(response)
except Exception as e:
    import traceback
    traceback.print_exc()

print("\n--- EJEMPLO 3: Enviar un correo ---")
query_envio = "Envia un correo a 'ampr2003@gmail.com' con el asunto 'Gracias por la ayuda' y el mensaje 'Gracias por la ayuda que me has prestado'."

try:
    response = agent.invoke({"messages": [{"role": "user", "content": query_envio}]})
    imprimir_respuesta_limpia(response)
except Exception as e:
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("--- EJEMPLO 4: MONITOREO DE CORREOS ENTRANTES (CORREGIDO) ---")
print("="*60)
print("🔍 El agente monitoreará los correos entrantes cada 30 segundos.")
print("⏹️  Presiona Ctrl+C para detener el monitoreo.\n")

import time
from datetime import datetime

try:
    contador_ciclo = 0
    while True:
        contador_ciclo += 1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"[{timestamp}] 🔄 Ciclo #{contador_ciclo} - Verificando nuevos correos...")

        query_monitor = (
            "Busca correos recibidos NO ELIMINADOS en los últimos 10 minutos. "
            "Si NO encuentras ningún correo en ese lapso, responde ÚNICAMENTE con la palabra 'SIN_NOVEDADES'. "
            "Si encuentras correos, dame un resumen con: Remitente, Asunto y resume el contenido del correo."
        )

        try:
            response = agent.invoke({"messages": [{"role": "user", "content": query_monitor}]})

            if response and "messages" in response:
                last_message = response["messages"][-1]
                content = last_message.content

                if isinstance(content, list):
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                    respuesta_texto = ''.join(text_parts)
                else:
                    respuesta_texto = str(content)

                if "SIN_NOVEDADES" in respuesta_texto:
                    print(f"   ✓ No hay correos nuevos (Sin novedades)\n")
                else:
                    print(f"\n📬 ¡NUEVOS CORREOS DETECTADOS!")
                    print("-" * 60)
                    print(respuesta_texto)
                    print("-" * 60 + "\n")

        except Exception as e:
            print(f"   ❌ Error al verificar correos: {e}\n")

        print(f"⏳ Esperando 30 segundos...\n")
        time.sleep(30)

except KeyboardInterrupt:
    print("\n\n🛑 Monitoreo detenido por el usuario.")