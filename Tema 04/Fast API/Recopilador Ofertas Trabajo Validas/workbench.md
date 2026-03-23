# **🛠️ Workbench: Recopilador Ofertas de Trabajo Válidas con el CV del Usuario**

Versión: 2.0.0  
Estado: ✅ **PRODUCCIÓN - Completamente Funcional**  
Objetivo: Automatizar la búsqueda de empleo mediante un agente autónomo que filtra correos de LinkedIn e InfoJobs, analiza ofertas web y notifica solo las oportunidades relevantes basándose en el CV del usuario.

## **1\. Arquitectura del Sistema**

El sistema funciona como un pipeline ETL (Extract, Transform, Load) enriquecido con Inteligencia Artificial Generativa, ejecutándose en un servidor web con Flask + threading para cumplir requisitos de plataformas PaaS.

### **Diagrama de Flujo de Datos**

1. **Contexto (Input Estático):** CV Usuario (PDF) → PyPDFLoader → Texto de Referencia.
2. **Disparador (Trigger):** Email LinkedIn/InfoJobs → GmailToolkit → URLs de Ofertas.
3. **Extracción (Scraping Cascada):** URL → Jina AI (intento 1) → FireCrawl (intento 2) → HTTP Directo (intento 3) → Markdown Limpio.
4. **Análisis (Cerebro IA - Doble Fase):** 
   - **Fase 1 (ATS):** Filtro por keywords técnicas y requisitos básicos
   - **Fase 2 (RRHH):** Evaluación semántica profunda de experiencia y soft skills
   - Output: Score 0-100 + Justificación + Datos estructurados (salario, empresa, fecha, etc.)
5. **Decisión:** Score >= 70 → Notificación | Score < 70 → Descartar silenciosamente
6. **Notificación (Output):** Match Positivo → Telegram Bot API → Mensaje enriquecido con iconos y formato visual.

## **2\. Stack Tecnológico**

Selección de herramientas basada en robustez y capacidad de integración con LangChain.

| Componente                | Herramienta                                  | Función Crítica                                                                                                       |
| :------------------------ | :------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------- |
| **Ingesta de Documentos** | **PyPDFLoader** (LangChain Community)        | Transformar el CV en formato PDF a texto plano para inyectarlo en el System Prompt del LLM.                           |
| **Fuente de Datos**       | **Gmail Toolkit** (LangChain Google)         | Leer correos, filtrar por remitente (LinkedIn/InfoJobs) y estado (unread), extraer enlaces y gestionar el estado de lectura. Incluye limpieza automática de correos >14 días.   |
| **Web Scraping (Cascada)**| **Jina AI Reader** (Gratuito, sin API key)  | Primer intento: Scraping rápido sin autenticación. Excelente para LinkedIn y páginas estáticas. |
|                           | **FireCrawl** (API Key requerida)           | Segundo intento: Navegar páginas dinámicas con JS, evadir detecciones y convertir HTML complejo en Markdown. Ideal para InfoJobs. |
|                           | **Requests + BeautifulSoup** (Built-in)      | Tercer intento: Scraping directo HTTP como último recurso. Manejo de reintentos con exponential backoff. |
| **Motor de IA**           | **Gemini 2.5 Flash** (Google AI Studio)      | Modelo orquestador. Implementa sistema de doble fase (ATS + RRHH) con anti-alucinación (grounding). Output estructurado via Pydantic. |
| **Notificaciones**        | **Telegram Bot API** (requests síncronos)    | Canal de comunicación directo y gratuito para enviar alertas urgentes al móvil del usuario con formato enriquecido (iconos, barras de progreso).                           |
| **Servidor Web**          | **Flask + Gunicorn**                         | Servidor HTTP para cumplir requisitos de Render/Railway. Endpoints: `/` (status) y `/health` (health check). Ejecuta bot en hilo secundario daemon. |
| **Containerización**      | **Docker** (Python 3.11-slim)                | Imagen optimizada con multi-stage build. Inyección de secretos vía variables de entorno (`entrypoint.sh`). |

## **3\. Lógica Detallada del Pipeline**

### **Fase A: Inicialización (Cold Start)**

_Se ejecuta una sola vez al arrancar el servicio._

1. El sistema busca el archivo cv_usuario.pdf en la raíz.
2. PyPDFLoader carga el archivo y extrae el texto.
3. Se crea la variable global USER_CONTEXT que contiene la experiencia, skills y expectativas del usuario.

### **Fase B: Bucle de Ejecución (Runtime Loop)**

_Se ejecuta periódicamente (configurable vía `POLLING_INTERVAL`, por defecto 10 min)._

1. **Refresco de Conexión Gmail:**
   - Se crea una **nueva instancia** de `GmailJobCollector` en cada ciclo
   - **Crítico**: `GmailToolkit` cachea la lista de correos al inicializarse. Sin reinicio, los correos nuevos NO se detectarían
   - También evita timeouts de sesión OAuth y problemas de tokens expirados
   - El toolkit de LangChain gestiona automáticamente el refresh token

2. **Limpieza Automática de Correos Antiguos:**
   - Query: `from:"linkedin OR infojobs" older_than:14d`
   - Mueve correos a papelera en lotes de 500 (batch processing)
   - Mantiene la bandeja de entrada limpia y evita procesamiento duplicado

3. **Monitorización de Email:**
   - Query: `from:("linkedin" OR "infojobs") label:UNREAD newer_than:14d ("empleos similares" OR "alertas de empleo" OR "Alerta de empleo InfoJobs")`
   - Si no hay correos: Dormir `POLLING_INTERVAL` segundos
   - Si hay correos (hasta 5 por ciclo):
     - Extraer URLs (manejo de tracking links y redirecciones)
     - Marcar correo como LEÍDO
     - Procesar cada URL

4. **Scraping Web (Estrategia en Cascada):**
   - **Intento 1 - Jina AI:**
     - URL: `https://r.jina.ai/{url}?t={timestamp}`
     - Headers con selectores CSS personalizados según dominio
     - Timeout: 15s
     - Si falla → Intento 2
   
   - **Intento 2 - FireCrawl:**
     - Cliente Python oficial con API key
     - Renderizado JavaScript completo
     - Extracción de Markdown limpio
     - Timeout: 30s
     - Si falla → Intento 3
   
   - **Intento 3 - HTTP Directo:**
     - Requests con User-Agent realista
     - Retry strategy: 3 intentos con exponential backoff
     - BeautifulSoup para parsing HTML básico
     - Si falla → Descartar oferta y continuar

5. **Análisis con IA (Cerebro - Gemini 2.5 Flash):**
   - **Sistema de Prompts Estructurado:**
     ```
     FASE 1 (ATS): Filtro por keywords técnicas + requisitos mínimos
       - Score < 60 → RECHAZADO (mensaje robótico)
       - Score >= 60 → Continuar a Fase 2
     
     FASE 2 (RRHH): Evaluación semántica profunda
       - Score 60-69 → RECHAZADO (mensaje profesional)
       - Score 70-79 → CANDIDATO APTO ✅
       - Score 80-89 → CANDIDATO FUERTE 🚀
       - Score 90-100 → CANDIDATO IDEAL 🔥
     ```
   
   - **Output Estructurado (Pydantic):**
     ```python
     {
       "match": bool,
       "match_score": int,
       "job_title": str,
       "company": str,
       "salary": str,
       "posted_date": str,
       "benefits": str,
       "summary": str
     }
     ```
   
   - **Sistema Anti-Alucinación (Grounding):**
     - Prohibición explícita de conocimiento externo
     - Todas las conclusiones deben estar presentes en el texto
     - Verificación de fecha real de publicación

6. **Decisión y Notificación:**
   - **Si Score < 70:**
     - Log silencioso: `[DESCARTADO] {summary[:50]}...`
     - No se notifica al usuario
   
   - **Si Score >= 70:**
     - Formateo de mensaje enriquecido:
       - Icono según score (🔥/🚀/✅/⚠️)
       - Barra de progreso visual (🟩🟩🟩⬜⬜)
       - Datos estructurados (título, empresa, salario, beneficios, fecha)
       - Justificación del match
       - Link directo para aplicar
     - Envío vía Telegram Bot API
     - Log: `[MATCH] Enviando alerta`

7. **Gestión de Errores:**
   - Errores de conexión Gmail: Reintento en 60s (evita crash)
   - Errores de scraping: Continuar con siguiente URL
   - Errores de Gemini: Log del error y continuar
   - Error crítico del bucle: Sleep 60s y reintentar

## **4\. Configuración del Entorno (.env)**

Variables necesarias para la ejecución. **No compartir este archivo ni commitearlo a Git.**

```env
# === GEMINI (Google AI Studio) ===
GEMINI_API_KEY="AIzaSy..."

# === TELEGRAM BOT ===
TELEGRAM_BOT_TOKEN="123456789:ABCdefGHI..."
TELEGRAM_CHAT_ID="987654321"

# === FIRECRAWL (Opcional pero recomendado) ===
FIRECRAWL_API_KEY="fc-..."

# === CONFIGURACION DEL SISTEMA ===
# Intervalo de polling en segundos (600 = 10 minutos)
POLLING_INTERVAL=600
```

### **4.1. Archivos de Credenciales Adicionales**

Además del `.env`, el sistema requiere:

1. **`credentials.json`** (OAuth 2.0 de Google Cloud Console)
   - Descargado desde Google Cloud Console → APIs & Services → Credentials
   - Tipo: "Desktop app"
   - APIs habilitadas: Gmail API + Generative Language API

2. **`token.json`** (Generado automáticamente)
   - Se crea ejecutando: `python src/setup_auth.py`
   - Contiene el access token y refresh token de OAuth
   - Válido por tiempo indefinido (mientras no se revoquen permisos)

3. **`data/cv_usuario.pdf`**
   - Tu CV en formato PDF
   - Debe tener texto seleccionable (no imagen escaneada)

## **5\. Estructura del Proyecto**

```
/Recopilador Ofertas Trabajo Validas
│
├── /data
│   └── cv_usuario.pdf              # Tu CV (Input) - NO commitear
│
├── /src
│   ├── loader.py                   # PyPDFLoader - Extracción de CV
│   ├── mail_agent.py               # Gmail Toolkit - Búsqueda y limpieza
│   ├── scraper.py                  # Estrategia de scraping en cascada
│   ├── brain.py                    # Gemini + Prompts + Pydantic schemas
│   ├── bot.py                      # Telegram notifier con formato rico
│   └── setup_auth.py               # CLI para generar token.json
│
├── main.py                         # Orquestador: Flask + Bot Thread
├── requirements.txt                # Dependencias Python
├── Dockerfile                      # Imagen Docker optimizada
├── entrypoint.sh                   # Script de inicialización (secretos)
├── .dockerignore                   # Excluir archivos sensibles del build
├── .gitignore                      # Excluir archivos sensibles del repo
├── .env                            # Variables de entorno - NO commitear
├── credentials.json                # OAuth Google - NO commitear
├── token.json                      # Token Gmail - NO commitear
├── workbench.md                    # Documentación técnica (este archivo)
└── README.md                       # Documentación de usuario
```

## **6\. Estado del Desarrollo**

### ✅ **Funcionalidades Implementadas**

1. ✅ **Carga de CV** (`loader.py`)
   - Extracción completa de texto de PDF multi-página
   - Verificación de archivo vacío
   - Fallback a ruta alternativa si no se encuentra

2. ✅ **Integración Gmail** (`mail_agent.py`)
   - Búsqueda de correos UNREAD de LinkedIn e InfoJobs (<14 días)
   - Limpieza automática de correos antiguos (>14 días)
   - Resolución de tracking links y redirecciones
   - Extracción de URLs tanto de LinkedIn como InfoJobs
   - Manejo robusto de errores de API

3. ✅ **Scraping Multi-Estrategia** (`scraper.py`)
   - Jina AI Reader (intento 1)
   - FireCrawl API (intento 2)
   - Scraping directo con requests + retry logic (intento 3)
   - Selectores CSS personalizados por dominio (LinkedIn, InfoJobs)
   - Limpieza de URLs (parámetros tracking, fragmentos)
   - Manejo de errores 422, 404, timeouts

4. ✅ **Análisis con IA** (`brain.py`)
   - Modelo: Gemini 2.5 Flash (temperature=0)
   - Sistema de doble fase (ATS → RRHH)
   - Output estructurado con Pydantic
   - Anti-alucinación con grounding explícito
   - Extracción de fecha literal del texto
   - Validación de vigencia de oferta

5. ✅ **Notificaciones Telegram** (`bot.py`)
   - Cliente síncrono (requests) para evitar conflictos de event loop
   - Formato enriquecido con:
     - Iconos según score (🔥/🚀/✅/⚠️)
     - Barra de progreso visual
     - Datos estructurados
     - Links directos
   - Manejo de errores de API

6. ✅ **Orquestación Principal** (`main.py`)
   - Servidor Flask con endpoints `/` y `/health`
   - Bot en hilo secundario daemon
   - Bucle infinito con gestión de errores
   - Logs detallados de cada fase
   - Refresco de Gmail client en cada ciclo

7. ✅ **Containerización** (`Dockerfile` + `entrypoint.sh`)
   - Imagen Python 3.11-slim optimizada
   - Multi-stage build para reducir tamaño
   - Inyección de secretos vía variables de entorno
   - Gunicorn para producción

8. ✅ **Autenticación OAuth** (`setup_auth.py`)
   - Script CLI para generación de token
   - Flujo OAuth completo automatizado
   - Instrucciones paso a paso

### 🚀 **Despliegue en Producción**

**Plataformas Soportadas:**
- ✅ Render (Free Tier) - Recomendado
- ✅ Railway
- ✅ Docker Local

**Estado:** Sistema probado y funcionando en entornos de desarrollo y producción.

### 📈 **Métricas de Rendimiento**

- **Tiempo de procesamiento por oferta:** ~5-15 segundos
  - Scraping: 2-8s (depende de la estrategia exitosa)
  - Análisis Gemini: 2-5s
  - Notificación Telegram: <1s

- **Uso de recursos:**
  - RAM: ~150-200 MB (Flask + Bot + dependencias)
  - CPU: Mínimo (mayoría del tiempo en sleep)
  - Red: Bajo (solo durante scraping y API calls)

- **Rate Limits:**
  - Gemini Free Tier: 15 RPM (requests per minute) / 1000 RPD (requests per day)
  - Gmail API: 250 cuota units/segundo (suficiente)
  - Jina AI: Sin límites conocidos
  - FireCrawl: Depende del plan contratado
  - Telegram: 30 mensajes/segundo por bot

### 🔧 **Mejoras Futuras (Opcional)**

- [ ] Base de datos SQLite para histórico de ofertas
- [ ] Dashboard web con Flask-Admin para visualización
- [ ] Soporte para más plataformas (Indeed, Glassdoor)
- [ ] Sistema de respuestas automáticas
- [ ] Integración con Notion/Trello
- [ ] Generación de cover letters con IA
- [ ] Análisis de tendencias salariales
- [ ] Sistema de feedback (usuario indica si match fue correcto)

---

## **7\. Notas Técnicas Importantes**

### **7.1. Por qué Flask + Threading**

Plataformas como Render requieren un servidor web HTTP que responda a health checks. Si solo ejecutáramos el bot en un script simple, Render lo marcaría como "crashed" tras unos segundos sin respuesta HTTP.

**Solución:** 
- Flask escucha en el puerto asignado por `$PORT`
- Bot se ejecuta en un hilo secundario daemon
- Ambos comparten el proceso principal

### **7.2. Por qué Reiniciar Gmail Client**

**Razón Principal - Caché Interno:**
`GmailToolkit` de LangChain guarda internamente un snapshot de los correos presentes en el momento de su inicialización. Si llegan nuevos correos después de crear la instancia, **NO serán detectados** hasta que se cree una nueva instancia del toolkit.

**Razones Secundarias:**
Los tokens OAuth pueden expirar o perder sincronización con la API. Crear una nueva instancia de `GmailJobCollector` en cada ciclo fuerza a LangChain a:
1. **Recargar la lista actualizada de correos** (incluye los recién llegados)
2. Verificar validez del token OAuth
3. Refrescar el token si es necesario
4. Crear nueva sesión HTTP

**Comportamiento sin reinicio:**
- Ciclo 1 (10:00): Se inicializa Gmail → Ve 0 correos
- Ciclo 2 (10:10): Reutiliza instancia → Sigue viendo 0 correos (aunque hayan llegado 3 nuevos)
- Ciclo 3 (10:20): Reutiliza instancia → Sigue viendo 0 correos

**Comportamiento con reinicio (actual):**
- Ciclo 1 (10:00): Nueva instancia → Ve 0 correos
- Ciclo 2 (10:10): Nueva instancia → Ve 3 correos nuevos ✅
- Ciclo 3 (10:20): Nueva instancia → Ve los correos que llegaron desde 10:10 ✅

Esto garantiza que el sistema detecte correos en tiempo real sin necesidad de reiniciar manualmente el servicio.

### **7.3. Estrategia de Scraping en Cascada**

**¿Por qué 3 métodos?**

- **Jina AI:** Rápido y gratuito, pero puede fallar en páginas muy dinámicas
- **FireCrawl:** Potente pero requiere API key de pago
- **Directo:** Último recurso, funciona en la mayoría de sitios estáticos

**Ventaja:** Alta disponibilidad. Si un servicio cae, los otros compensan.

### **7.4. Sistema de Grounding (Anti-Alucinación)**

El prompt de Gemini incluye instrucciones explícitas:
```
⚠️ INSTRUCCIONES DE GROUNDING:
1. Tu análisis debe basarse ÚNICA Y EXCLUSIVAMENTE en el contenido de "TEXTO DE LA WEB"
2. PROHIBIDO usar conocimiento externo o suposiciones
3. Debes extraer la fecha de publicación REAL del texto
```

Esto reduce drásticamente las alucinaciones del modelo, especialmente en:
- Salarios no especificados
- Fechas inventadas
- Beneficios no mencionados

### **7.5. Selectores CSS Personalizados**

InfoJobs tiene una estructura HTML compleja con múltiples contenedores. Los selectores actuales fueron obtenidos mediante:
1. Inspección del DOM con DevTools
2. Pruebas iterativas con diferentes combinaciones
3. Validación de contenido extraído

**Selectores actuales (InfoJobs):**
```css
target: #job-description-container, .ij-OfferDetailHeader, h1, .subtitle
remove: header.global-header, footer, .ij-Share, .ij-Report, #demand-button-container
```

Si InfoJobs cambia su estructura, estos selectores deberán actualizarse.
