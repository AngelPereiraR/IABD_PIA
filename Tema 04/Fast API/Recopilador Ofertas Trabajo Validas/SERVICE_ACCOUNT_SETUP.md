# 🔐 Configurar Service Account para Gmail (Automático)

> **TL;DR**: Con Service Account el bot funciona 100% automático sin expiración de tokens.

## 📋 Paso 1: Crear Service Account en Google Cloud

### 1.1 Accede a Google Cloud Console
1. Ve a https://console.cloud.google.com/
2. Selecciona tu proyecto (o crea uno nuevo)
3. Habilita **Gmail API** si aún no lo has hecho:
   - Búsqueda: "Gmail API"
   - Click en "Habilitar"

### 1.2 Crear la Service Account
1. **IAM y administración** → **Cuentas de servicio**
2. **Crear cuenta de servicio**
3. Rellena:
   ```
   Nombre: recruitment-bot
   ID: recruitment-bot (se auto-genera)
   Descripción: Bot para monitorizar ofertas de trabajo
   ```
4. Click en **Crear y continuar**
5. Permisos (opcional, skip si no tienes rol específico)
6. Click en **Continuar** → **Finalizar**

### 1.3 Descargar la Clave JSON
1. En la lista de cuentas de servicio, haz click en la que creaste
2. Pestaña **Claves**
3. **Agregar clave** → **Crear clave nueva** → **JSON**
4. Se descarga automáticamente `[project-id]-[hash].json`
5. **Renómbralo a `service-account.json`**
6. **Colócalo en la raíz del proyecto** (misma carpeta que `main.py`)

**Estructura esperada:**
```
/Recopilador Ofertas Trabajo Validas/
├── main.py
├── service-account.json          ← AQUÍ
├── requirements.txt
├── src/
│   ├── mail_agent.py
│   ├── token_manager.py
│   └── ...
└── ...
```

---

## 🔗 Paso 2: Compartir tu Gmail con el Service Account

### Opción A: Si usas Google Workspace (Recomendado) 🏢

Habilita **Domain-Wide Delegation** para que el bot acceda a gmail automáticamente:

1. En Google Cloud Console → Tu Service Account → **Detalles**
2. Copia el **Client ID** (número grande)
3. Ve a **Google Workspace Admin** → **Controles de seguridad** → **Administración de acceso de terceros**
4. **Agregar nuevo cliente OAuth:**
   ```
   Client ID: [Pega el número]
   Alcances autorizados:
     - https://www.googleapis.com/auth/gmail.readonly
     - https://www.googleapis.com/auth/gmail.modify
   ```
5. En `src/token_manager.py`, descomenta esta línea en `get_credentials()`:
   ```python
   creds = creds.with_subject("tu-email@tu-dominio.com")
   ```

### Opción B: Si usas Gmail Personal 👤

**Problema**: Google no permite que Service Accounts accedan a Gmail personal directamente.

**Soluciones**:

#### Solución B1: Usar una dirección de Gmail creada para el bot
1. Crea una cuenta de Gmail nueva: `recruitment-bot@gmail.com`
2. En tu cuenta principal, configura que los correos de LinkedIn/InfoJobs se reenvíen a esa cuenta
3. Usa esa cuenta de Gmail para el Service Account

#### Solución B2: Mantener OAuth 2.0
Si prefieres seguir con OAuth:
1. Simplemente no incluyas `service-account.json`
2. Usa `python src/setup_auth.py` para generar `token.json`
3. El bot usará OAuth automáticamente

---

## ✅ Paso 3: Verificar que Funciona

### Test Local
```bash
python main.py
```

Deberías ver:
```
[TOKEN] Service Account encontrado. Credenciales válidas.
[TOKEN] Usando Service Account...
[BUSQUEDA] Buscando alertas recientes...
```

### En Producción (Render/HF Spaces)

1. Sube `service-account.json` a tu repositorio **PRIVADO**, o
2. Copia el contenido del JSON en una variable de entorno:
   ```
   SERVICE_ACCOUNT_JSON={"type": "service_account", ...}
   ```

Entonces el `token_manager.py` lo buscará automáticamente.

---

## 🔄 Migración desde OAuth a Service Account

Si ya tienes `token.json`:

1. **Descarga** `service-account.json` desde Google Cloud
2. **Colócalo** en la raíz del proyecto
3. **Elimina o ignora** `token.json`
4. **Ejecuta** `python main.py`

El `TokenManager` automáticamente detectará `service-account.json` y lo usará en lugar de OAuth.

---

## ❓ Preguntas Frecuentes

**P: ¿Se expira el Service Account?**  
R: No, nunca. Las credenciales son permanentes.

**P: ¿Es más seguro que OAuth?**  
R: Sí, no almacenas tokens en `token.json`. Las credenciales están protegidas por Google Cloud.

**P: ¿Puedo usar ambos?**  
R: Sí. Si existe `service-account.json` lo usa; si no, intenta OAuth.

**P: ¿Y si uso Google Workspace?**  
R: Usa Domain-Wide Delegation (Opción A). Es la forma recomendada.

---

## 📚 Referencias

- [Google Cloud Service Account Docs](https://cloud.google.com/iam/docs/service-accounts)
- [Gmail API](https://developers.google.com/gmail/api)
- [Domain-Wide Delegation](https://developers.google.com/identity/protocols/oauth2/service-account#delegatingauthority)
