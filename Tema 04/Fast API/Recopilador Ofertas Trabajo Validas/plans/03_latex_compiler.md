# Plan 03: Motor de Compilación LaTeX

## Objetivo
Crear `src/latex_compiler.py`: recibe contenido `.tex` como string, lo escribe en disco, ejecuta `pdflatex`, y retorna la ruta del PDF generado.

## Prerrequisitos
- Plan 00 completado (Dockerfile con `texlive-full`)
- `pdflatex` disponible en el sistema (dentro del contenedor Docker)

---

## Paso 1: Verificar disponibilidad de pdflatex

```bash
# Dentro del contenedor Docker:
which pdflatex
pdflatex --version
```

Si no está disponible localmente (desarrollo en Windows), usar Docker:
```bash
docker run --rm -v $(pwd)/data:/data texlive/texlive pdflatex /data/test.tex
```

---

## Paso 2: Crear `src/latex_compiler.py`

```python
import asyncio
import os
import tempfile
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

async def compile_latex(tex_content: str, offer_id: int) -> str:
    """
    Compila contenido LaTeX a PDF.
    
    Args:
        tex_content: Contenido del archivo .tex como string
        offer_id: ID de la oferta (para nombre único del archivo)
    
    Returns:
        Ruta absoluta al PDF generado
    
    Raises:
        RuntimeError: Si pdflatex falla
    """
    # Directorio temporal aislado por oferta
    work_dir = Path(tempfile.mkdtemp(prefix=f"cv_{offer_id}_"))
    tex_path = work_dir / "cv.tex"
    pdf_path = work_dir / "cv.pdf"
    
    try:
        # 1. Escribir .tex
        tex_path.write_text(tex_content, encoding="utf-8")
        logger.info(f"[LaTeX] .tex escrito en {tex_path}")
        
        # 2. Primera pasada (genera aux, toc)
        await _run_pdflatex(tex_path, work_dir)
        
        # 3. Segunda pasada (resuelve referencias cruzadas)
        await _run_pdflatex(tex_path, work_dir)
        
        # 4. Verificar PDF generado
        if not pdf_path.exists():
            log_content = _read_log(work_dir / "cv.log")
            raise RuntimeError(f"PDF no generado. Log:\n{log_content}")
        
        logger.info(f"[LaTeX] PDF generado: {pdf_path} ({pdf_path.stat().st_size} bytes)")
        
        # 5. Copiar a directorio persistente (work_dir se borrará)
        output_dir = Path("data/generated")
        output_dir.mkdir(exist_ok=True)
        final_path = output_dir / f"cv_offer_{offer_id}.pdf"
        shutil.copy2(pdf_path, final_path)
        
        return str(final_path)
        
    finally:
        # Limpiar directorio temporal
        shutil.rmtree(work_dir, ignore_errors=True)


async def _run_pdflatex(tex_path: Path, work_dir: Path):
    """Ejecuta pdflatex de forma asíncrona."""
    cmd = [
        "pdflatex",
        "-interaction=nonstopmode",  # No pausar en errores
        "-halt-on-error",            # Salir con código != 0 si hay error
        f"-output-directory={work_dir}",
        str(tex_path)
    ]
    
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(work_dir)
    )
    
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
    
    if proc.returncode != 0:
        log_content = _read_log(work_dir / "cv.log")
        raise RuntimeError(
            f"pdflatex falló (código {proc.returncode}).\n"
            f"stderr: {stderr.decode()}\n"
            f"Log: {log_content[-2000:]}"  # Últimas 2000 chars del log
        )


def _read_log(log_path: Path) -> str:
    """Lee el log de pdflatex para diagnóstico de errores."""
    if log_path.exists():
        return log_path.read_text(encoding="utf-8", errors="ignore")
    return "(log no disponible)"
```

---

## Paso 3: Manejo de errores LaTeX comunes

### Caracteres especiales en LaTeX
El engine debe escapar estos caracteres en el contenido generado por DeepSeek:

```python
# Añadir a src/engine.py, aplicar antes de _render_template()
LATEX_SPECIAL = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "\\": r"\textbackslash{}",
}

def escape_latex(text: str) -> str:
    """Escapa caracteres especiales para LaTeX."""
    for char, escaped in LATEX_SPECIAL.items():
        text = text.replace(char, escaped)
    return text
```

> **Importante**: Aplicar `escape_latex()` SOLO a los campos de texto libre (resumen, descripciones), NO al código LaTeX generado (itemize, etc.) que ya incluye comandos LaTeX.

---

## Paso 4: Compilación de prueba

### 4.1 Plantilla mínima de test

```bash
cat > /tmp/test_cv.tex << 'EOF'
\documentclass{article}
\usepackage[utf8]{inputenc}
\begin{document}
\title{Test CV}
\author{Test User}
\maketitle
Sección de prueba: Python, FastAPI, PostgreSQL.
\end{document}
EOF
```

### 4.2 Test del módulo

```bash
python -c "
import asyncio
from src.latex_compiler import compile_latex

async def test():
    tex = open('/tmp/test_cv.tex').read()
    pdf_path = await compile_latex(tex, offer_id=0)
    print(f'OK - PDF en: {pdf_path}')

asyncio.run(test())
"
```

### 4.3 Test con oferta real (integración)

```bash
python -c "
import asyncio
from src.engine import generate_cv

async def test():
    url = await generate_cv(offer_id=1)
    print(f'OK - URL Cloudinary: {url}')

asyncio.run(test())
"
```

---

## Paso 5: Consideraciones de rendimiento

| Aspecto | Detalle |
|---------|---------|
| Tiempo compilación | ~5-15s por PDF (depende de la complejidad) |
| RAM necesaria | ~200MB por proceso pdflatex |
| Concurrencia | Limitar a 3-4 compilaciones simultáneas |
| Timeout | 120s por pasada (configurado en `wait_for`) |
| Limpieza | `work_dir` se borra en `finally` siempre |

### Semáforo para limitar concurrencia (opcional)

```python
# En main.py, crear semáforo global
latex_semaphore = asyncio.Semaphore(3)

# En latex_compiler.py, wrappear compile_latex:
async def compile_latex_safe(tex_content: str, offer_id: int) -> str:
    from main import latex_semaphore
    async with latex_semaphore:
        return await compile_latex(tex_content, offer_id)
```

---

## Archivos Creados/Modificados

| Archivo | Acción |
|---------|--------|
| `src/latex_compiler.py` | Crear - compilación async con pdflatex |
| `src/engine.py` | Añadir `escape_latex()`, integrar compiler |
| `data/generated/` | Directorio para PDFs generados (gitignore) |
| `Dockerfile` | Ya incluye `texlive-full` (ver Plan 00) |

## `.gitignore` - añadir

```
data/generated/
*.aux
*.log
*.out
*.toc
```
