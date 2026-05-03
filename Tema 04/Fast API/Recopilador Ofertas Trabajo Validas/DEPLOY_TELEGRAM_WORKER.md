# Deploying Telegram Worker to Render

## Overview
El **Worker de Telegram** procesa la cola de mensajes en BD y reintenta envios indefinidamente.
- **Dockerfile:** `Dockerfile.worker`
- **Script:** `telegram_worker.py`
- **Recursos:** ~50MB (muy ligero, free tier de Render es suficiente)

## Pasos de Deployment en Render

### 1. Crear nuevo servicio en Render
- Ve a [render.com](https://render.com)
- Click en "New +" → "Web Service"
- Conecta tu repositorio de GitHub

### 2. Configurar el servicio

| Campo | Valor |
|-------|-------|
| **Name** | `telegram-worker` |
| **Environment** | `Docker` |
| **Dockerfile Path** | `Dockerfile.worker` |
| **Plan** | `Free` (suficiente) |

### 3. Configurar variables de entorno

En **Environment Variables**, añade:

```
DATABASE_URL=postgresql+psycopg2://[user]:[password]@[host]/[db]
TELEGRAM_BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh
TELEGRAM_CHAT_ID=987654321
```

**Nota:** Usa la misma `DATABASE_URL`, `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` que en HF Spaces.

### 4. Deploy

- Click en "Create Web Service"
- Render hará build y deployment automático
- En los logs verás:
  ```
  [TELEGRAM WORKER] Iniciando worker...
  [TELEGRAM WORKER] Procesando cola cada 30 segundos...
  ```

## Flujo de Mensajes

```
HF Spaces (Bot)
    ↓ Guarda mensaje en BD
PostgreSQL (Neon)
    ↓ Render Lee cada 30s
Render Worker
    ↓ Intenta enviar
Telegram API
    ↓
Tu chat
```

## Monitoreo

En Render:
- **Logs:** Ve los intentos de envío
- **Health:** El worker debe estar "Running" (verde)

En BD:
- Query para ver estado:
  ```sql
  SELECT id, status, retries FROM telegram_notifications ORDER BY created_at DESC LIMIT 10;
  ```

## Troubleshooting

**"Build failed"**
- Verifica que `requirements.txt` esté en la raíz
- Verifica que `src/` contenga los módulos necesarios

**"Worker en crash loop"**
- Verifica `DATABASE_URL` en variables de entorno
- Verifica que `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` sean correctos

**Mensajes siguen sin llegar**
- Verifica logs en Render
- Verifica estado en BD: `SELECT status, COUNT(*) FROM telegram_notifications GROUP BY status;`

## Auto-restart

Render reinicia automáticamente el servicio si falla. El worker es resiliente:
- Caída de DB → reintenta
- Timeout de Telegram → reintenta
- Error cualquiera → logged y continúa
