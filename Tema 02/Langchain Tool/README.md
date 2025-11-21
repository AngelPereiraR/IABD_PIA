# Langchain Gmail Tool

Este proyecto implementa un agente de LangChain capaz de interactuar con Gmail para leer, buscar y enviar correos electrónicos, utilizando modelos generativos de Google (Gemini).

## Requisitos Previos

- **Python 3.10+** instalado.
- Una cuenta de **Google Cloud Platform (GCP)** con la API de Gmail habilitada.
- Una **API Key de Google Gemini**.

## Configuración

### 1. Clonar el repositorio (o descargar los archivos)

Asegúrate de tener los siguientes archivos en tu directorio:

- `gmail_tool.py`
- `requirements.txt`
- `.env.template`
- `credentials.json` (Ver paso 3)

### 2. Instalar Dependencias

Se recomienda usar un entorno virtual:

```bash
python -m venv venv
# En Windows:
.\venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate
```

Instala las librerías necesarias:

```bash
pip install -r requirements.txt
```

### 3. Configurar Credenciales de Google (OAuth)

Para que el agente pueda acceder a tu Gmail, necesitas un archivo `credentials.json` de OAuth 2.0:

1. Ve a la [Consola de Google Cloud](https://console.cloud.google.com/).
2. Crea un nuevo proyecto o selecciona uno existente.
3. Habilita la **Gmail API**.
4. Ve a **Credenciales** > **Crear credenciales** > **ID de cliente de OAuth**.
5. Configura la pantalla de consentimiento (si es la primera vez).
6. Selecciona **Aplicación de escritorio**.
7. Descarga el archivo JSON, renómbralo a `credentials.json` y colócalo en la misma carpeta que `gmail_tool.py`.

> **Nota**: La primera vez que ejecutes el script, se abrirá una ventana del navegador para que inicies sesión y autorices la aplicación. Esto generará un archivo `token.json` automáticamente.

### 4. Configurar Variables de Entorno

1. Copia el archivo `.env.template` y renómbralo a `.env`:

    ```bash
    cp .env.template .env
    # O en Windows CMD:
    copy .env.template .env
    ```

2. Abre el archivo `.env` y pega tu API Key de Gemini:

    ```env
    GEMINI_API_KEY="PON_AQUI_TU_API_KEY"
    ```

## Uso

Ejecuta el script principal:

```bash
python gmail_tool.py
```

El script realizará varias acciones de demostración:

1. Configurará el agente.
2. Leerá correos (Ejemplo 1).
3. (Opcional) Creará borradores o enviará correos si descomentas las secciones correspondientes en el código.
4. Iniciará un bucle de monitoreo para buscar nuevos correos cada 30 segundos.

Para detener el monitoreo, presiona `Ctrl+C`.
