# Plan 02: Módulo de Procesamiento e IA (Engine)

## Objetivo
Crear `src/engine.py`: dado un `job_offer_id`, descarga el CV Maestro de Cloudinary, analiza la oferta con DeepSeek, y genera un `.tex` con el CV adaptado listo para compilar.

## Prerrequisitos
- Plan 00 completado (Cloudinary SDK en `src/storage.py`)
- Plan 01 completado (`src/brain.py` con `OfferAnalysis` disponible)
- CV Maestro subido a Cloudinary (público_id: `cv/master`)
- Plantilla LaTeX base disponible en `data/cv_template.tex`

---

## Paso 1: Plantilla LaTeX base

### 1.1 Crear `data/cv_template.tex`

La plantilla usa placeholders `{{VARIABLE}}` que el engine sustituirá:

```latex
\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{geometry}
\geometry{margin=1.5cm}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{titlesec}

% ---- Datos personales ----
\newcommand{\nombre}{{{NOMBRE}}}
\newcommand{\email}{{{EMAIL}}}
\newcommand{\linkedin}{{{LINKEDIN}}}
\newcommand{\github}{{{GITHUB}}}

\begin{document}

% ---- Cabecera ----
\begin{center}
  {\LARGE \textbf{\nombre}} \\[4pt]
  \email\ $|$\ \href{https://linkedin.com/in/\linkedin}{linkedin.com/in/\linkedin}\ $|$\ \href{https://github.com/\github}{github.com/\github}
\end{center}

\hrule\vspace{6pt}

% ---- Resumen ----
\section*{Resumen}
{{RESUMEN}}

% ---- Habilidades ----
\section*{Habilidades Técnicas}
{{HABILIDADES}}

% ---- Experiencia ----
\section*{Experiencia}
{{EXPERIENCIA}}

% ---- Formación ----
\section*{Formación}
{{FORMACION}}

% ---- Proyectos ----
\section*{Proyectos Destacados}
{{PROYECTOS}}

\end{document}
```

### 1.2 Crear `data/cv_master_data.json`

Datos estructurados del CV Maestro (fuente de verdad para el engine):

```json
{
  "nombre": "Nombre Apellido",
  "email": "correo@ejemplo.com",
  "linkedin": "tu-perfil",
  "github": "tu-usuario",
  "resumen_base": "Párrafo de presentación base del candidato.",
  "formacion": [
    {
      "titulo": "CFGS IABD",
      "centro": "Centro Educativo",
      "anio": "2024-2026"
    }
  ],
  "proyectos": [
    {
      "nombre": "OptiCV Engine",
      "descripcion": "Sistema de monitorización y generación de CVs con IA",
      "tecnologias": ["FastAPI", "LangChain", "PostgreSQL"]
    }
  ],
  "experiencia_base": [],
  "habilidades_base": {
    "lenguajes": ["Python", "SQL", "JavaScript"],
    "frameworks": ["FastAPI", "LangChain", "React"],
    "herramientas": ["Docker", "Git", "PostgreSQL"]
  }
}
```

---

## Paso 2: Crear `src/engine.py`

### 2.1 Dependencias del módulo

```python
import os
import json
import asyncio
import tempfile
import httpx
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Optional
from src.storage import upload_pdf
from src.database import AsyncSessionLocal, JobOffer
from sqlalchemy import select
```

### 2.2 Modelo de salida del análisis JD

```python
class AdaptedCVSections(BaseModel):
    resumen: str = Field(description="Párrafo resumen adaptado a esta oferta específica (3-5 frases)")
    habilidades: str = Field(
        description="Sección de habilidades en formato LaTeX itemize, priorizando las requeridas por la oferta"
    )
    experiencia: str = Field(
        description="Sección experiencia en formato LaTeX. Destacar logros relevantes para esta oferta."
    )
    keywords_destacados: list[str] = Field(
        description="Top 5 keywords de la oferta que se han integrado en el CV"
    )
```

### 2.3 Función principal `generate_cv`

```python
async def generate_cv(offer_id: int) -> str:
    """
    Genera CV optimizado para una oferta.
    Retorna URL de Cloudinary del PDF generado.
    """
    # 1. Cargar oferta desde BD
    offer = await _get_offer(offer_id)
    if not offer:
        raise ValueError(f"Oferta {offer_id} no encontrada")
    
    # 2. Actualizar estado
    await _update_status(offer_id, "processing")
    
    try:
        # 3. Cargar datos del CV Maestro
        master_data = _load_master_data()
        
        # 4. Adaptar secciones con DeepSeek
        adapted = await _adapt_cv_sections(offer.raw_text, master_data)
        
        # 5. Generar .tex con datos adaptados
        tex_content = _render_template(master_data, adapted)
        
        # 6. Compilar PDF (delegar a latex_compiler)
        from src.latex_compiler import compile_latex
        pdf_path = await compile_latex(tex_content, offer_id)
        
        # 7. Subir a Cloudinary
        cv_url = upload_pdf(pdf_path, f"cv/optimized/offer_{offer_id}")
        
        # 8. Guardar URL en BD
        await _update_cv_url(offer_id, cv_url)
        
        return cv_url
        
    except Exception as e:
        await _update_status(offer_id, "error")
        raise

async def _get_offer(offer_id: int) -> Optional[JobOffer]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(JobOffer).where(JobOffer.id == offer_id)
        )
        return result.scalar_one_or_none()

async def _update_status(offer_id: int, status: str):
    from sqlalchemy import update
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(JobOffer).where(JobOffer.id == offer_id).values(status=status)
        )
        await session.commit()

async def _update_cv_url(offer_id: int, url: str):
    from sqlalchemy import update
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(JobOffer).where(JobOffer.id == offer_id).values(
                optimized_cv_url=url, status="done"
            )
        )
        await session.commit()

def _load_master_data() -> dict:
    with open("data/cv_master_data.json", encoding="utf-8") as f:
        return json.load(f)
```

### 2.4 Función de adaptación con LangChain

```python
async def _adapt_cv_sections(offer_text: str, master_data: dict) -> AdaptedCVSections:
    """Usa DeepSeek para adaptar las secciones del CV a la oferta."""
    from langchain.output_parsers import PydanticOutputParser
    
    llm = ChatOpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat",
        temperature=0.3
    )
    parser = PydanticOutputParser(pydantic_object=AdaptedCVSections)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Eres experto en optimización de CVs para ATS y reclutadores técnicos.
Dado el perfil base del candidato y una oferta de trabajo, adapta las secciones del CV.

REGLAS:
- No inventes experiencia que no existe en el perfil base
- Reordena y enfatiza habilidades relevantes para la oferta
- Usa verbos de acción en el resumen
- Integra keywords de la oferta de forma natural
- Formato LaTeX válido en las secciones habilidades y experiencia
- Idioma: español

{format_instructions}"""),
        ("human", """PERFIL BASE:
{master_data}

OFERTA:
{offer_text}""")
    ])
    
    chain = prompt | llm | parser
    
    return await chain.ainvoke({
        "master_data": json.dumps(master_data, ensure_ascii=False, indent=2),
        "offer_text": offer_text,
        "format_instructions": parser.get_format_instructions()
    })
```

### 2.5 Función de renderizado de plantilla

```python
def _render_template(master_data: dict, adapted: AdaptedCVSections) -> str:
    """Sustituye placeholders en la plantilla LaTeX."""
    with open("data/cv_template.tex", encoding="utf-8") as f:
        template = f.read()
    
    # Formatear formación
    formacion_tex = ""
    for edu in master_data["formacion"]:
        formacion_tex += f"\\textbf{{{edu['titulo']}}} — {edu['centro']} ({edu['anio']})\\\\\n"
    
    # Formatear proyectos
    proyectos_tex = "\\begin{itemize}[nosep]\n"
    for p in master_data["proyectos"]:
        techs = ", ".join(p["tecnologias"])
        proyectos_tex += f"  \\item \\textbf{{{p['nombre']}}}: {p['descripcion']} ({techs})\n"
    proyectos_tex += "\\end{itemize}"
    
    replacements = {
        "{{NOMBRE}}": master_data["nombre"],
        "{{EMAIL}}": master_data["email"],
        "{{LINKEDIN}}": master_data["linkedin"],
        "{{GITHUB}}": master_data["github"],
        "{{RESUMEN}}": adapted.resumen,
        "{{HABILIDADES}}": adapted.habilidades,
        "{{EXPERIENCIA}}": adapted.experiencia,
        "{{FORMACION}}": formacion_tex,
        "{{PROYECTOS}}": proyectos_tex,
    }
    
    for placeholder, value in replacements.items():
        template = template.replace(placeholder, value)
    
    return template
```

---

## Paso 3: Verificación del módulo

```bash
# Test completo del engine (requiere oferta en BD y CV maestro configurado)
python -c "
import asyncio
from src.engine import generate_cv

async def test():
    # Usar ID de una oferta real en BD
    url = await generate_cv(1)
    print(f'CV generado: {url}')

asyncio.run(test())
"
```

---

## Archivos Creados/Modificados

| Archivo | Acción |
|---------|--------|
| `src/engine.py` | Crear - lógica principal de adaptación |
| `data/cv_template.tex` | Crear - plantilla LaTeX con placeholders |
| `data/cv_master_data.json` | Crear - datos estructurados del CV maestro |
