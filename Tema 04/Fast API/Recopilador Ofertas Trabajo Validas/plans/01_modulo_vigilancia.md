# Plan 01: Módulo de Vigilancia (Worker/Bot)

## Objetivo
Evolucionar el bot actual para persistir ofertas válidas en Neon y añadir botón inline en Telegram que dispare la generación de CV optimizado.

## Prerrequisitos
- Plan 00 completado (BD Neon + `src/database.py` disponible)
- Bot Telegram funcional con token configurado
- LangChain + DeepSeek API key disponibles

---

## Paso 1: Implementar LangChain + DeepSeek en `src/brain.py`

### 1.1 Stack de análisis

| Componente | Tecnología |
|----------|-----------|
| LLM Provider | `langchain-openai` + DeepSeek endpoint |
| Prompting | LangChain ChatPromptTemplate |
| Parsing | PydanticOutputParser |
| Output Model | `OfferAnalysis` Pydantic |

### 1.2 Nuevo `src/brain.py`

```python
import os
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import Optional

class OfferAnalysis(BaseModel):
    is_relevant: bool = Field(description="True si la oferta encaja con el perfil del CV")
    score: int = Field(description="Puntuación 0-100 de adecuación al perfil")
    job_title: str = Field(description="Título del puesto extraído")
    company: str = Field(description="Nombre de la empresa")
    salary: Optional[str] = Field(description="Salario mencionado, o null si no aparece")
    key_skills: list[str] = Field(description="Lista de habilidades clave requeridas")
    rejection_reason: Optional[str] = Field(description="Motivo de rechazo si is_relevant=False")
    summary: str = Field(description="Resumen breve de la oferta en 2-3 frases")

def build_chain():
    llm = ChatOpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat",
        temperature=0.1
    )
    parser = PydanticOutputParser(pydantic_object=OfferAnalysis)
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Eres un evaluador experto en selección de personal técnica (IA/Data).
Analiza la oferta de trabajo y el CV del candidato.
Evalúa en dos fases:
1. ATS: ¿Contiene las palabras clave mínimas del CV?
2. Recruiter: ¿Es genuinamente adecuada para el perfil?

{format_instructions}"""),
        ("human", "CV del candidato:\n{cv}\n\nOferta de trabajo:\n{offer_text}")
    ])
    return prompt | llm | parser, parser

_chain, _parser = build_chain()

def analyze_offer(offer_text: str, cv_text: str) -> OfferAnalysis:
    """Analiza una oferta contra el CV. Retorna OfferAnalysis."""
    return _chain.invoke({
        "cv": cv_text,
        "offer_text": offer_text,
        "format_instructions": _parser.get_format_instructions()
    })
```

### 1.3 Actualizar `loader.py` para retornar texto plano
```python
# Asegurar que cv_text() retorna str, no bytes
def load_cv_text() -> str:
    import fitz  # PyMuPDF
    doc = fitz.open("data/cv_usuario.pdf")
    return "\n".join(page.get_text() for page in doc)
```

---

## Paso 2: Persistir ofertas en Neon desde `src/mail_agent.py`

### 2.1 Añadir función `save_offer_to_db`

```python
# Al final de mail_agent.py, añadir:
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import JobOffer, AsyncSessionLocal
import asyncio

async def save_offer_to_db(analysis, offer_url: str, raw_text: str, user_id: str) -> int:
    """Persiste una oferta analizada en Neon. Retorna el ID generado."""
    async with AsyncSessionLocal() as session:
        offer = JobOffer(
            user_id=user_id,
            job_title=analysis.job_title,
            company=analysis.company,
            raw_text=raw_text,
            offer_url=offer_url,
            score=analysis.score,
            status="pending"
        )
        session.add(offer)
        await session.commit()
        await session.refresh(offer)
        return offer.id
```

### 2.2 Integrar en el flujo principal del mail agent

```python
# En el loop principal, después de analyze_offer():
if analysis.is_relevant:
    offer_id = asyncio.run(save_offer_to_db(
        analysis=analysis,
        offer_url=url,
        raw_text=offer_text,
        user_id=USER_ID  # UUID del usuario único en la BD
    ))
    await bot.send_offer(analysis, offer_id)
```

> **Nota**: `USER_ID` puede ser un UUID fijo en `.env` para uso personal, o derivarse del `telegram_id`.

---

## Paso 3: Añadir botón inline "Generar CV" en `src/bot.py`

### 3.1 Actualizar `send_offer` para incluir InlineKeyboardMarkup

```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def send_offer(analysis, offer_id: int):
    """Envía notificación con botón para generar CV optimizado."""
    
    # Barra de progreso visual (existente)
    filled = int(analysis.score / 10)
    bar = "█" * filled + "░" * (10 - filled)
    
    text = (
        f"🎯 *{analysis.job_title}* — {analysis.company}\n"
        f"📊 Score: `{bar}` {analysis.score}/100\n"
        f"💰 {analysis.salary or 'Salario no indicado'}\n\n"
        f"{analysis.summary}\n\n"
        f"🔑 Skills: {', '.join(analysis.key_skills[:5])}"
    )
    
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "📄 Generar CV Optimizado",
            callback_data=f"gen_cv:{offer_id}"
        )
    ]])
    
    await bot_instance.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )
```

### 3.2 Añadir handler para el callback

```python
from telegram.ext import Application, CallbackQueryHandler
import httpx

async def handle_generate_cv(update, context):
    """Procesa el botón 'Generar CV Optimizado'."""
    query = update.callback_query
    await query.answer()
    
    offer_id = query.data.split(":")[1]
    await query.edit_message_text(f"⏳ Generando CV optimizado para oferta #{offer_id}...")
    
    # Llamar al endpoint FastAPI
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"http://localhost:7860/api/generate/{offer_id}",
            timeout=300  # 5 min - compilación LaTeX puede tardar
        )
    
    if resp.status_code == 200:
        cv_url = resp.json()["cv_url"]
        await query.edit_message_text(
            f"✅ CV generado\n📎 [Descargar PDF]({cv_url})",
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text("❌ Error generando CV. Revisa los logs.")

# Registrar handler en Application
app.add_handler(CallbackQueryHandler(handle_generate_cv, pattern="^gen_cv:"))
```

---

## Paso 4: Gestión del USER_ID único

Para uso personal (un solo usuario), añadir a `.env`:
```env
USER_ID=<uuid-generado>
```

Generar UUID:
```bash
python -c "import uuid; print(uuid.uuid4())"
```

Insertar usuario base en Neon:
```sql
INSERT INTO users (id, email, telegram_id)
VALUES ('<uuid>', 'tu@email.com', '<telegram_chat_id>');
```

---

## Verificación del Módulo

```bash
# 1. Brain con DeepSeek retorna análisis válido
python -c "
from src.brain import analyze_offer
from src.loader import load_cv_text
cv = load_cv_text()
result = analyze_offer('Buscamos Data Scientist con Python y ML', cv)
print(f'Score: {result.score}, Relevante: {result.is_relevant}')
"

# 2. Oferta se guarda en BD
python -c "
import asyncio
from src.database import AsyncSessionLocal, JobOffer
from sqlalchemy import select

async def test():
    async with AsyncSessionLocal() as s:
        result = await s.execute(select(JobOffer).limit(5))
        offers = result.scalars().all()
        print(f'Ofertas en BD: {len(offers)}')
asyncio.run(test())
"

# 3. Bot envía mensaje con botón (test manual)
# Ejecutar main.py y verificar que llega mensaje con botón inline en Telegram
```

## Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `src/brain.py` | Implementar LangChain + DeepSeek, modelo Pydantic |
| `src/mail_agent.py` | Añadir `save_offer_to_db`, integrar en flujo |
| `src/bot.py` | Añadir botón inline, handler callback, httpx call |
| `src/loader.py` | Verificar retorno como str plano |
| `.env` / HF Secrets | Añadir `USER_ID`, `DEEPSEEK_API_KEY` |
