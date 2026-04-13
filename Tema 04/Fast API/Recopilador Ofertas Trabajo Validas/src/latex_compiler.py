"""
LaTeX Compiler Module - Compiles .tex content to PDF asynchronously.

Receives LaTeX content as string, writes to isolated temp directory,
executes pdflatex (2 passes), and returns the path to the generated PDF.
"""
import asyncio
import logging
import shutil
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# Output directory for generated PDFs (persistent across requests)
OUTPUT_DIR = Path("data/generated")


async def compile_latex(tex_content: str, offer_id: int) -> str:
    """
    Compila contenido LaTeX a PDF.

    Args:
        tex_content: Contenido del archivo .tex como string
        offer_id: ID de la oferta (para nombre único del archivo)

    Returns:
        Ruta absoluta al PDF generado en data/generated/

    Raises:
        RuntimeError: Si pdflatex falla en cualquiera de las dos pasadas
    """
    work_dir = Path(tempfile.mkdtemp(prefix=f"cv_{offer_id}_"))
    tex_path = work_dir / "cv.tex"
    pdf_path = work_dir / "cv.pdf"

    try:
        # 1. Escribir .tex en directorio de trabajo aislado
        tex_path.write_text(tex_content, encoding="utf-8")
        logger.info(f"[LaTeX] .tex escrito en {tex_path}")

        # 2. Primera pasada (genera .aux, .toc, referencias)
        await _run_pdflatex(tex_path, work_dir)

        # 3. Segunda pasada (resuelve referencias cruzadas)
        await _run_pdflatex(tex_path, work_dir)

        # 4. Verificar que el PDF fue generado
        if not pdf_path.exists():
            log_content = _read_log(work_dir / "cv.log")
            raise RuntimeError(f"PDF no generado. Log:\n{log_content}")

        logger.info(f"[LaTeX] PDF generado: {pdf_path} ({pdf_path.stat().st_size} bytes)")

        # 5. Copiar a directorio persistente antes de borrar tmpdir
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        final_path = OUTPUT_DIR / f"cv_offer_{offer_id}.pdf"
        shutil.copy2(pdf_path, final_path)

        return str(final_path)

    finally:
        # Limpiar siempre el directorio temporal
        shutil.rmtree(work_dir, ignore_errors=True)


async def _run_pdflatex(tex_path: Path, work_dir: Path) -> None:
    """
    Ejecuta pdflatex de forma asíncrona con timeout.

    Args:
        tex_path: Ruta al archivo .tex
        work_dir: Directorio de trabajo y salida

    Raises:
        RuntimeError: Si pdflatex retorna código != 0 o supera el timeout
    """
    cmd = [
        "pdflatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        f"-output-directory={work_dir}",
        str(tex_path),
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(work_dir),
    )

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        raise RuntimeError(
            f"pdflatex excedió el timeout de 120s para {tex_path.name}"
        )

    if proc.returncode != 0:
        log_content = _read_log(work_dir / "cv.log")
        raise RuntimeError(
            f"pdflatex falló (código {proc.returncode}).\n"
            f"stderr: {stderr.decode(errors='replace')}\n"
            f"Log (últimas 2000 chars):\n{log_content[-2000:]}"
        )


def _read_log(log_path: Path) -> str:
    """
    Lee el log de pdflatex para diagnóstico de errores.

    Args:
        log_path: Ruta al archivo .log generado por pdflatex

    Returns:
        Contenido del log, o mensaje indicando que no está disponible
    """
    if log_path.exists():
        return log_path.read_text(encoding="utf-8", errors="ignore")
    return "(log no disponible)"
