"""
Tests para Plan 03 - Motor de Compilación LaTeX

Cubre:
1. escape_latex() - todos los caracteres especiales
2. compile_latex() - compilación real con tex mínimo (requiere pdflatex)
3. _run_pdflatex() - fallo con .tex inválido
4. _read_log() - lectura de log existente y no existente
5. Integración CVGenerator._compile_latex → latex_compiler
"""

import asyncio
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Agregar proyecto root al path
sys.path.insert(0, str(Path(__file__).parent.parent))
os.chdir(Path(__file__).parent.parent)

from src.cv_generator import CVGenerator
from src.latex_compiler import _read_log, compile_latex, _run_pdflatex

PDFLATEX_AVAILABLE = False
try:
    import subprocess
    r = subprocess.run(["pdflatex", "--version"], capture_output=True, timeout=5)
    PDFLATEX_AVAILABLE = r.returncode == 0
except Exception:
    pass

MINIMAL_TEX = r"""
\documentclass{article}
\usepackage[utf8]{inputenc}
\begin{document}
Test CV: Python, FastAPI, PostgreSQL.
\end{document}
"""

INVALID_TEX = r"""
\documentclass{article}
\begin{document}
\unknowncommand{broken}
\end{document}
"""


# ---------------------------------------------------------------------------
# Tests: escape_latex
# ---------------------------------------------------------------------------

class TestEscapeLatex(unittest.TestCase):
    """Tests unitarios para CVGenerator.escape_latex()"""

    def test_ampersand(self):
        self.assertEqual(CVGenerator.escape_latex("A & B"), r"A \& B")

    def test_percent(self):
        self.assertEqual(CVGenerator.escape_latex("100%"), r"100\%")

    def test_dollar(self):
        self.assertEqual(CVGenerator.escape_latex("$100"), r"\$100")

    def test_hash(self):
        self.assertEqual(CVGenerator.escape_latex("#tag"), r"\#tag")

    def test_underscore(self):
        self.assertEqual(CVGenerator.escape_latex("snake_case"), r"snake\_case")

    def test_braces(self):
        self.assertEqual(CVGenerator.escape_latex("{value}"), r"\{value\}")

    def test_caret(self):
        self.assertIn(r"\textasciicircum", CVGenerator.escape_latex("x^2"))

    def test_tilde(self):
        self.assertIn(r"\textasciitilde", CVGenerator.escape_latex("~dir"))

    def test_backslash(self):
        self.assertIn(r"\textbackslash", CVGenerator.escape_latex("a\\b"))

    def test_non_string_input(self):
        """Debe convertir tipos no-str a str sin lanzar excepción"""
        result = CVGenerator.escape_latex(42)
        self.assertEqual(result, "42")

    def test_clean_string_unchanged(self):
        """Texto sin caracteres especiales no debe modificarse"""
        text = "Desarrollador Python con experiencia en FastAPI"
        self.assertEqual(CVGenerator.escape_latex(text), text)

    def test_multiple_specials(self):
        """Múltiples caracteres especiales en el mismo string"""
        result = CVGenerator.escape_latex("email@host.com 50% & más")
        self.assertIn(r"\%", result)
        self.assertIn(r"\&", result)


# ---------------------------------------------------------------------------
# Tests: _read_log
# ---------------------------------------------------------------------------

class TestReadLog(unittest.TestCase):
    """Tests unitarios para latex_compiler._read_log()"""

    def test_existing_log(self):
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False, encoding="utf-8") as f:
            f.write("This is a pdflatex log\n! Error on line 5\n")
            tmp_path = Path(f.name)
        try:
            content = _read_log(tmp_path)
            self.assertIn("Error on line 5", content)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_missing_log_returns_placeholder(self):
        result = _read_log(Path("/nonexistent/path/cv.log"))
        self.assertEqual(result, "(log no disponible)")


# ---------------------------------------------------------------------------
# Tests: compile_latex (unitarios con mock)
# ---------------------------------------------------------------------------

class TestCompileLatexUnit(unittest.TestCase):
    """Tests unitarios de compile_latex usando mocks (sin pdflatex real)"""

    def test_compile_latex_calls_run_pdflatex_twice(self):
        """compile_latex debe llamar a _run_pdflatex exactamente 2 veces"""
        call_count = 0

        async def mock_run_pdflatex(tex_path, work_dir):
            nonlocal call_count
            call_count += 1
            # Crear un PDF falso para que compile_latex no falle en el check
            pdf = work_dir / "cv.pdf"
            pdf.write_bytes(b"%PDF-1.4 fake")

        async def run():
            with patch("src.latex_compiler._run_pdflatex", side_effect=mock_run_pdflatex):
                result = await compile_latex(MINIMAL_TEX, offer_id=999)
            return result

        result = asyncio.run(run())
        self.assertEqual(call_count, 2)
        self.assertIn("cv_offer_999.pdf", result)

        # Cleanup
        generated = Path("data/generated/cv_offer_999.pdf")
        generated.unlink(missing_ok=True)

    def test_compile_latex_cleans_tmpdir(self):
        """El directorio temporal debe borrarse aunque falle la compilación"""
        created_dirs = []

        original_mkdtemp = __import__("tempfile").mkdtemp

        def mock_mkdtemp(**kwargs):
            d = original_mkdtemp(**kwargs)
            created_dirs.append(d)
            return d

        async def mock_run_pdflatex(tex_path, work_dir):
            raise RuntimeError("pdflatex falló (simulado)")

        async def run():
            with patch("src.latex_compiler.tempfile.mkdtemp", side_effect=mock_mkdtemp), \
                 patch("src.latex_compiler._run_pdflatex", side_effect=mock_run_pdflatex):
                try:
                    await compile_latex(MINIMAL_TEX, offer_id=998)
                except RuntimeError:
                    pass

        asyncio.run(run())

        for d in created_dirs:
            self.assertFalse(
                Path(d).exists(),
                f"Directorio temporal {d} no fue eliminado"
            )

    def test_compile_latex_raises_if_pdf_missing(self):
        """Si _run_pdflatex no genera el PDF, debe lanzar RuntimeError"""
        async def mock_run_pdflatex(tex_path, work_dir):
            pass  # No crea cv.pdf

        async def run():
            with patch("src.latex_compiler._run_pdflatex", side_effect=mock_run_pdflatex):
                await compile_latex(MINIMAL_TEX, offer_id=997)

        with self.assertRaises(RuntimeError):
            asyncio.run(run())


# ---------------------------------------------------------------------------
# Tests: integración real con pdflatex
# ---------------------------------------------------------------------------

def _run_with_proactor(coro):
    """Ejecuta una corrutina con ProactorEventLoop (necesario en Windows para subprocess)."""
    loop = asyncio.ProactorEventLoop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@unittest.skipUnless(PDFLATEX_AVAILABLE, "pdflatex no disponible en este sistema")
class TestCompileLatexIntegration(unittest.TestCase):
    """Tests de integración que requieren pdflatex instalado"""

    def test_compile_minimal_tex(self):
        """Debe compilar un .tex mínimo y retornar ruta a PDF existente"""
        pdf_path = _run_with_proactor(compile_latex(MINIMAL_TEX, offer_id=0))
        p = Path(pdf_path)
        self.assertTrue(p.exists(), f"PDF no encontrado en {pdf_path}")
        self.assertGreater(p.stat().st_size, 0, "PDF generado está vacío")
        p.unlink(missing_ok=True)

    def test_compile_invalid_tex_raises(self):
        r"""Un .tex con \unknowncommand debe lanzar RuntimeError"""
        with self.assertRaises(RuntimeError):
            _run_with_proactor(compile_latex(INVALID_TEX, offer_id=1))

    def test_output_dir_created(self):
        """data/generated/ debe crearse automáticamente"""
        import shutil
        generated = Path("data/generated")
        if generated.exists():
            shutil.rmtree(generated)

        pdf_path = _run_with_proactor(compile_latex(MINIMAL_TEX, offer_id=2))
        self.assertTrue(generated.exists())
        Path(pdf_path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Tests: CVGenerator._build_latex_template aplica escape_latex
# ---------------------------------------------------------------------------

class TestBuildLatexTemplateEscaping(unittest.TestCase):
    """Verifica que _build_latex_template escapa datos personales"""

    def _make_offer_user(self):
        offer = MagicMock()
        offer.raw_text = "oferta de prueba"
        user = MagicMock()
        user.email = "test@example.com"
        return offer, user

    def test_nombre_con_special_chars_escapado(self):
        offer, user = self._make_offer_user()
        master_data = {"nombre": "O'Brien & Associates"}
        result = CVGenerator._build_latex_template(offer, user, master_data)
        # El & debe estar escapado en el contenido LaTeX
        self.assertNotIn("O'Brien & Associates", result)
        self.assertIn(r"\&", result)

    def test_email_sin_specials_no_modificado(self):
        offer, user = self._make_offer_user()
        master_data = {"email": "user@example.com"}
        result = CVGenerator._build_latex_template(offer, user, master_data)
        self.assertIn("user@example.com", result)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
