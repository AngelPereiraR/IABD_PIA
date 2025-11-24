# **🛠️ Workbench: Recopilador Ofertas de Trabajo Válidas con el CV del Usuario**

Versión: 1.0.0  
Estado: Diseño de Arquitectura  
Objetivo: Automatizar la búsqueda de empleo mediante un agente autónomo que filtra correos de LinkedIn, analiza ofertas web y notifica solo las oportunidades relevantes basándose en el CV del usuario.

## **1\. Arquitectura del Sistema**

El sistema funciona como un pipeline ETL (Extract, Transform, Load) enriquecido con Inteligencia Artificial Generativa.

### **Diagrama de Flujo de Datos**

1. **Contexto (Input Estático):** CV Usuario (PDF) → PyPDFLoader → Texto de Referencia.
2. **Disparador (Trigger):** Email LinkedIn → GmailToolkit → URL de la Oferta.
3. **Extracción (Scraping):** URL → FireCrawl → Markdown Limpio.
4. **Análisis (Cerebro):** Markdown \+ Texto CV → Gemma-3-27b → Decisión (Match/No Match).
5. **Notificación (Output):** Match Positivo → Telegram Bot API → Mensaje al usuario.

## **2\. Stack Tecnológico**

Selección de herramientas basada en robustez y capacidad de integración con LangChain.

| Componente                | Herramienta                           | Función Crítica                                                                                                       |
| :------------------------ | :------------------------------------ | :-------------------------------------------------------------------------------------------------------------------- |
| **Ingesta de Documentos** | **PyPDFLoader** (LangChain Community) | Transformar el CV en formato PDF a texto plano para inyectarlo en el System Prompt del LLM.                           |
| **Fuente de Datos**       | **Gmail Toolkit** (LangChain Google)  | Leer correos, filtrar por remitente (linkedin) y estado (unread), extraer enlaces y gestionar el estado de lectura.   |
| **Web Scraping**          | **FireCrawl**                         | Navegar páginas dinámicas de LinkedIn, evadir detecciones básicas y convertir HTML complejo en Markdown estructurado. |
| **Motor de IA**           | **Gemma-3-27b** (Google AI Studio)    | Modelo orquestador. Compara semánticamente los requisitos de la oferta con las habilidades del CV.                    |
| **Notificaciones**        | **Telegram Bot API**                  | Canal de comunicación directo y gratuito para enviar alertas urgentes al móvil del usuario.                           |

## **3\. Lógica Detallada del Pipeline**

### **Fase A: Inicialización (Cold Start)**

_Se ejecuta una sola vez al arrancar el servicio._

1. El sistema busca el archivo cv_usuario.pdf en la raíz.
2. PyPDFLoader carga el archivo y extrae el texto.
3. Se crea la variable global USER_CONTEXT que contiene la experiencia, skills y expectativas del usuario.

### **Fase B: Bucle de Ejecución (Runtime Loop)**

_Se ejecuta periódicamente (ej. cada 15 min)._

1. **Monitorización de Email:**
   - Query: from:linkedin "job alert" is:unread
   - Si no hay correos: Dormir X minutos.
   - Si hay correo: Extraer URL del botón "Ver empleo" y marcar correo como LEÍDO.
2. **Navegación Web (FireCrawl):**
   - Enviar URL a FireCrawl.
   - Recibir page_content en formato Markdown (ignorando navbars, footers y ads).
3. **Razonamiento (Gemma-3):**
   - Prompt: "Actúa como reclutador senior. Tienes el CV del candidato en USER_CONTEXT. Analiza la siguiente oferta: OFFER_MARKDOWN. Decide si hay match (\>70%). Responde en JSON."
4. **Acción:**
   - **Si Match \== False:** Loguear "Descartado" y continuar.
   - **Si Match \== True:** Formatear mensaje y enviar vía Telegram API al CHAT_ID del usuario.

## **4\. Configuración del Entorno (.env)**

Variables necesarias para la ejecución. **No compartir este archivo.**

```
# Google AI Studio (LLM)
GOOGLE_API_KEY="AIzaSy..."

# Google Cloud / Gmail API
GOOGLE_APPLICATION_CREDENTIALS="credentials.json"

# FireCrawl (Scraping)
FIRECRAWL_API_KEY="fc_..."

# Telegram Bot
TELEGRAM_BOT_TOKEN="123456:ABC-..."
TELEGRAM_CHAT_ID="987654321"
```

## **5\. Estructura del Proyecto**

```
/reclutador-ia
│
├── /data
│ └── cv_usuario.pdf \# Tu CV (Input)
│
├── /src
│ ├── \_\_init\_\_.py
│ ├── loader.py \# Lógica de PyPDFLoader
│ ├── mail_agent.py \# Lógica de Gmail Toolkit
│ ├── scraper.py \# Cliente FireCrawl
│ ├── brain.py \# Cliente Gemma-3 \+ Prompts
│ └── bot.py \# Cliente Telegram
│
├── main.py \# Orquestador del bucle principal
├── requirements.txt \# Dependencias
├── .env \# Secretos
└── README.md \# Documentación
```

## **6\. Siguientes Pasos de Implementación**

1. **Configurar Credenciales:** Obtener credentials.json de Google Cloud Console (API Gmail habilitada).
2. **Entorno Python:** Crear virtualenv e instalar paquetes (langchain, firecrawl-py, google-generativeai).
3. **Prueba Unitaria 1:** Script simple que lea el PDF e imprima el texto.
4. **Prueba Unitaria 2:** Script que lea el último email de LinkedIn y saque la URL.
5. **Integración:** Conectar las piezas en main.py.
