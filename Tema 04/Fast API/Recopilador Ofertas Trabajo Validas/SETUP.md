# Setup OptiCV Engine - Guía Completa

Instrucciones paso a paso para obtener todas las credenciales y configurar el proyecto.

---

## 🔴 PASO 1: Base de Datos Neon (PostgreSQL)

**Tiempo:** ~5 min | **Costo:** Free tier disponible

### 1.1 Crear cuenta en Neon

1. Ir a [neon.tech](https://neon.tech)
2. Click **Sign Up** → Google/GitHub OAuth
3. Crear nuevo **Project** (nombre: `opticv`)
4. Seleccionar región: `US East` (más barato)
5. Crear database: `opticv` (default)

### 1.2 Obtener CONNECTION STRING

1. En Neon Dashboard → **Project** → **Connection**
2. Copiar la URL que empieza con `postgresql://`
3. Formato: `postgresql://[user]:[password]@[host]/[dbname]`

**Guardar en `.env`:**
```env
DATABASE_URL="postgresql://user:password@ep-xxxx.us-east-1.neon.tech/opticv"
```

### 1.3 Crear tablas (primera vez)

```bash
python -c "
import asyncio
from src.database import init_db

asyncio.run(init_db())
"
```

Si no hay error, estás listo ✅

---

## 🔴 PASO 2: Cloudinary (Storage de Archivos)

**Tiempo:** ~5 min | **Costo:** Free tier: 25 GB

### 2.1 Crear cuenta en Cloudinary

1. Ir a [cloudinary.com](https://cloudinary.com)
2. Sign Up → Email/GitHub
3. Confirmar email

### 2.2 Obtener credenciales

1. Dashboard → **Settings** → **API Keys**
2. Copiar:
   - **Cloud Name** (ej: `dvxxxx`)
   - **API Key** (ej: `123456789...`)
   - **API Secret** (ej: `abcdef...`)

**Guardar en `.env`:**
```env
CLOUDINARY_CLOUD_NAME="dvxxxx"
CLOUDINARY_API_KEY="123456789000"
CLOUDINARY_API_SECRET="abcdef1234567890"
```

### 2.3 Verificar conexión

```bash
python -c "
from src.storage import upload_bytes
data = b'TEST PDF CONTENT'
url = upload_bytes(data, 'test/cv_maestro_test')
print(f'OK - URL: {url}')
"
```

Si no hay error, estás listo ✅

---

## 🟡 PASO 3: DeepSeek API (Análisis IA)

**Tiempo:** ~10 min | **Costo:** Modelo barato (~$0.15 por 1M tokens)

### 3.1 Crear cuenta en DeepSeek

1. Ir a [platform.deepseek.com](https://platform.deepseek.com)
2. Click **Sign Up** → Email
3. Confirmar email

### 3.2 Obtener API Key

1. Dashboard → **API Keys**
2. Click **Create new API key**
3. Copiar la clave completa

**Guardar en `.env`:**
```env
DEEPSEEK_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 3.3 Configurar créditos (opcional)

- Ir a **Billing** → **Top up Balance**
- Usar tarjeta de crédito (Visa/Mastercard)
- Mínimo: $5 USD

**Cálculo de costos:**
- Analizar oferta: ~500 tokens → $0.0001
- Generar CV adaptado: ~2000 tokens → $0.0003
- Costo total por CV: ~$0.0005 (muy barato)

---

## 🟡 PASO 4: Jina AI (Extracción Web)

**Tiempo:** ~5 min | **Costo:** Free tier disponible

### 4.1 Crear cuenta en Jina

1. Ir a [api.jina.ai](https://api.jina.ai)
2. Sign Up → Email
3. Confirmar email

### 4.2 Obtener API Key

1. Dashboard → **API Keys**
2. Copiar la clave (formato: `jina_xxxxx...`)

**Guardar en `.env`:**
```env
JINA_API_KEY="jina_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 4.3 Verificar cuota

- Free tier: 50 llamadas/mes
- Para desarrollo es suficiente
- Producción: upgrade a pagado (~$20/mes para 10k llamadas)

---

## 🟡 PASO 5: FireCrawl (Scraping de respaldo)

**Tiempo:** ~5 min | **Costo:** Free tier disponible

### 5.1 Crear cuenta en FireCrawl

1. Ir a [firecrawl.dev](https://firecrawl.dev)
2. Sign Up → Email/GitHub
3. Confirmar email

### 5.2 Obtener API Key

1. Dashboard → **API Keys**
2. Copiar clave (formato: `fc_xxxxx...`)

**Guardar en `.env`:**
```env
FIRECRAWL_API_KEY="fc_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 5.3 Propósito

- **Jina** es el primario (rápido, >90% éxito)
- **FireCrawl** es el respaldo (lento, +JavaScript rendering)
- Si Jina falla → intenta FireCrawl

---

## 🟡 PASO 6: Telegram Bot (Notificaciones)

**Tiempo:** ~5 min | **Costo:** Gratis

### 6.1 Crear el Bot

1. Abrir Telegram → buscar **@BotFather**
2. Enviar `/start`
3. Enviar `/newbot`
4. Dar nombre: `OptiCV Engine`
5. Dar username: `opticv_engine_bot` (ej)
6. Copiar **Token** (formato: `123456:ABC-DEF...`)

**Guardar en `.env`:**
```env
TELEGRAM_BOT_TOKEN="123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh"
```

### 6.2 Obtener tu CHAT_ID

1. Abrir tu bot (username que creaste)
2. Enviar `/start` (cualquier mensaje)
3. Abrir en navegador: `https://api.telegram.org/bot[TOKEN]/getUpdates`
4. Buscar `"chat":{"id":XXXXXXXX}` → copiar ese número

**Guardar en `.env`:**
```env
TELEGRAM_CHAT_ID="987654321"
```

### 6.3 Prueba de conexión

```bash
python -c "
from src.bot import TelegramNotifier
bot = TelegramNotifier()
bot.send_match_alert({'url': 'https://test.com'}, {
    'match': True,
    'score': 85,
    'summary': 'Test message'
})
print('OK - Mensaje enviado a Telegram')
"
```

Si recibes el mensaje en Telegram, estás listo ✅

---

## 🟡 PASO 7: Google (Gmail)

**Tiempo:** ~15 min | **Costo:** Gratis

### 7.1 Crear credenciales en Google Cloud

1. Ir a [console.cloud.google.com](https://console.cloud.google.com)
2. Crear nuevo **Project** (nombre: `opticv`)
3. Ir a **APIs & Services** → **Enable APIs**
4. Buscar y habilitar:
   - ✅ **Gmail API**

### 7.2 Crear Service Account (para lectura de Gmail)

1. **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **Service Account**
3. Nombre: `opticv-bot`
4. Click **Create**
5. En Service Account creada → **Keys** → **Add Key** → **Create new key**
6. Tipo: **JSON**
7. Descargar `credentials.json`

**Contenido será así:**
```json
{
  "type": "service_account",
  "project_id": "opticv-xxxxx",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  ...
}
```

**Guardar en `.env` (todo en UNA línea, sin saltos):**
```env
GOOGLE_CREDENTIALS_JSON='{"type":"service_account","project_id":"opticv-xxxxx",...}'
```

### 7.3 Generar token OAuth (primera vez)

```bash
# Esto abre un navegador para autorizar
python src/setup_auth.py
```

Seleccionar cuenta de Gmail → permitir acceso → se genera `token.json`

**Extraer contenido de token.json y guardar en `.env`:**
```env
GOOGLE_TOKEN_JSON='{"access_token":"ya29.xxxxx","token_type":"Bearer",...}'
```

---

## 📝 ARCHIVO FINAL .env

Copiar `.env.template` → `.env` y rellenar:

```bash
# Base de datos
DATABASE_URL="postgresql://user:pass@host/opticv"

# Cloudinary
CLOUDINARY_CLOUD_NAME="dvxxxx"
CLOUDINARY_API_KEY="123456789"
CLOUDINARY_API_SECRET="abc123"

# IA
DEEPSEEK_API_KEY="sk-xxx"

# Scraping
JINA_API_KEY="jina_xxx"
FIRECRAWL_API_KEY="fc_xxx"

# Telegram
TELEGRAM_BOT_TOKEN="123456:ABC"
TELEGRAM_CHAT_ID="987654321"

# Google
GOOGLE_CREDENTIALS_JSON='{"type":"service_account",...}'
GOOGLE_TOKEN_JSON='{"access_token":"ya29.xxx",...}'

# Servidor
PORT=7860

# Usuario (opcional)
USER_ID="123e4567-e89b-12d3-a456-426614174000"
```

---

## ✅ VERIFICACIÓN FINAL

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Inicializar BD
python -c "
import asyncio
from src.database import init_db
asyncio.run(init_db())
"

# 3. Verificar Cloudinary
python -c "from src.storage import upload_bytes; print('✅ Cloudinary OK')"

# 4. Verificar Telegram
python -c "from src.bot import TelegramNotifier; print('✅ Telegram OK')"

# 5. Iniciar servidor
python main.py

# 6. Abrir navegador
# http://localhost:7860/ → debe responder con "Reclutador IA está vivo..."
# http://localhost:7860/health → debe responder con "OK"
```

Si todo funciona, ¡estás listo para Plan 01! 🚀

---

## 🆘 Troubleshooting

| Error | Solución |
|-------|----------|
| `ModuleNotFoundError: langchain` | `pip install -r requirements.txt` |
| `SQLALCHEMY_SILENCE_UBER_WARNING` | Normal, ignorar (warning de SQLAlchemy) |
| `Database connection failed` | Verificar `DATABASE_URL` en `.env` |
| `CloudinaryError: unauthorized` | Verificar `CLOUDINARY_API_KEY` y `API_SECRET` |
| `Telegram bot not responding` | Verificar `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` |
| `DeepSeek API error: 401` | Verificar `DEEPSEEK_API_KEY` y que tenga crédito |
| `Port 7860 already in use` | Cambiar en `.env`: `PORT=8000` |

---

## 📚 Links Útiles

- [Neon Docs](https://neon.tech/docs)
- [Cloudinary Docs](https://cloudinary.com/documentation)
- [DeepSeek API](https://platform.deepseek.com)
- [Jina API](https://api.jina.ai)
- [FireCrawl](https://firecrawl.dev)
- [Telegram Bot API](https://core.telegram.org/bots)
- [Google Cloud Console](https://console.cloud.google.com)

---

## ⏱️ Tiempo Total Estimado

- Base de datos: 5 min
- Cloudinary: 5 min
- DeepSeek: 10 min
- Jina: 5 min
- FireCrawl: 5 min
- Telegram: 5 min
- Google: 15 min
- **Total: ~45 minutos**

Una vez completado, el proyecto está listo para producción en HF Spaces o Render. ✅
