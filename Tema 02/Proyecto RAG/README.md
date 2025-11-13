# Proyecto RAG TEA Andalucía

## Descripción

Este proyecto implementa un sistema de **Retrieval-Augmented Generation (RAG)** especializado en proporcionar información precisa y actualizada sobre trámites, ayudas y derechos relacionados con el **Trastorno del Espectro Autista (TEA)** en Andalucía. Utiliza inteligencia artificial para consultar una base de datos vectorial de documentos oficiales, ofreciendo respuestas contextuales y fundamentadas en normativas autonómicas y estatales.

El sistema está diseñado para:

- Facilitar el acceso a información oficial sobre TEA en Andalucía
- Proporcionar respuestas claras y accesibles para familias y profesionales
- Mantener un historial de conversación para consultas contextuales
- Basarse exclusivamente en fuentes documentales verificadas

**⚠️ Importante:** Esta herramienta es informativa y no sustituye el asesoramiento profesional de trabajadores sociales, abogados o personal de la administración pública.

## Características

- **Motor RAG Avanzado**: Utiliza LangChain con retriever consciente del historial para consultas contextuales
- **Embeddings de Google**: Emplea modelos de embeddings de Google Generative AI para una representación semántica precisa
- **Base de Datos Vectorial**: Almacena y recupera información usando FAISS para búsquedas eficientes
- **Interfaz Gráfica**: Aplicación web interactiva construida con Streamlit
- **Fuentes Oficiales**: Basado en documentación de la Junta de Andalucía, BOE y asociaciones especializadas
- **Historial de Conversación**: Mantiene contexto en consultas consecutivas

## Instalación

### Prerrequisitos

- Python 3.8 o superior
- Cuenta de Google AI Studio con API key de Gemini

### Pasos de Instalación

1. **Clona el repositorio**:

   ```bash
   git clone https://github.com/AngelPereiraR/IABD_PIA.git
   cd "IABD_PIA/Tema 02/Proyecto RAG"
   ```

2. **Instala las dependencias**:

   ```bash
   pip install langchain langchain-google-genai langchain-community faiss-cpu streamlit python-dotenv
   ```

3. **Configura las variables de entorno**:

   - Crea un archivo `.env` en la raíz del proyecto
   - Agrega tu API key de Google Gemini:
     ```
     GEMINI_API_KEY=tu_api_key_aqui
     ```

4. **Prepara los datos** (si no están incluidos):
   - Ejecuta los scripts de procesamiento de datos en orden:
     ```bash
     python extractor_datos.py
     python limpia_datos.py
     python chunker_datos.py
     python embeddings_generador.py
     ```

## Uso

### Interfaz Gráfica (Recomendado)

Para ejecutar la aplicación web interactiva:

```bash
streamlit run interfaz_grafica.py
```

La aplicación se abrirá en tu navegador predeterminado. Puedes hacer consultas sobre TEA en Andalucía y el sistema mantendrá el historial de la conversación.

### Uso Programático

```python
from motor_rag import TeaRagEngine

# Inicializar el motor
engine = TeaRagEngine()

# Hacer una consulta
respuesta = engine.get_answer("¿Qué trámites necesito para atención temprana?")
print(respuesta["answer"])

# Limpiar historial si es necesario
engine.clear_history()
```

### Scripts Individuales

- `extractor_datos.py`: Extrae texto de documentos PDF y TXT
- `limpia_datos.py`: Limpia y normaliza el texto extraído
- `chunker_datos.py`: Divide el texto en fragmentos (chunks) para procesamiento
- `embeddings_generador.py`: Genera embeddings y crea el índice FAISS
- `motor_rag.py`: Motor principal del sistema RAG

## Estructura del Proyecto

El proyecto se encuentra dentro del directorio `Tema 02/Proyecto RAG` del repositorio principal:

```
Tema 02/
└── Proyecto RAG/
    ├── motor_rag.py                 # Motor RAG principal
    ├── interfaz_grafica.py          # Interfaz web con Streamlit
    ├── extractor_datos.py           # Extracción de datos de documentos
    ├── limpia_datos.py              # Limpieza de datos
    ├── chunker_datos.py             # Creación de chunks
    ├── embeddings_generador.py      # Generación de embeddings y FAISS
    ├── chunks_tea_andalucia.jsonl   # Chunks de datos procesados
    ├── faiss_index_tea/             # Índice vectorial FAISS
    │   └── index.faiss
    ├── documentos_tea_andalucia/    # Documentos fuente originales
    ├── documentos_tea_andalucia_limpio/  # Documentos procesados
    └── Marco legal y fuentes .md    # Documentación de fuentes
```

## Fuentes de Información

El sistema se basa en documentación oficial incluyendo:

- **Normativa Autonómica**: Leyes de Educación, Atención Temprana, Discapacidad
- **Procedimientos Oficiales**: Guías de trámites de la Junta de Andalucía
- **Recursos Educativos**: Información sobre escolarización y apoyos educativos
- **Asociaciones**: Recursos de Autismo Andalucía y entidades colaboradoras

Para más detalles, consulta el archivo `Marco legal y fuentes .md`.

## Actualización de Datos

La documentación base fue recopilada hasta noviembre de 2025. Para actualizar:

1. Agrega nuevos documentos a `documentos_tea_andalucia/`
2. Ejecuta los scripts de procesamiento
3. Regenera el índice FAISS
