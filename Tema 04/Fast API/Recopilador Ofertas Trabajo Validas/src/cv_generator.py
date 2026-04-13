"""
CV Generator Module - Generates optimized CVs from job offer context.

Combines LaTeX templates with DeepSeek analysis to create personalized PDFs.
Uploads to Cloudinary for persistent storage.
"""
import os
import json
import asyncio
import tempfile
from pathlib import Path
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel as PydanticModel, Field

from src.storage import upload_pdf
from src.database import AsyncSessionLocal, JobOffer, User
from sqlalchemy import select


class AdaptedCVSections(PydanticModel):
    """Modelo de secciones CV adaptadas por DeepSeek a una oferta específica."""
    resumen: str = Field(description="Párrafo resumen adaptado a la oferta (3-5 frases, verbos de acción)")
    habilidades: str = Field(description="Sección habilidades en formato LaTeX itemize, priorizando skills de la oferta")
    experiencia: str = Field(description="Sección experiencia en formato LaTeX, destacando logros relevantes para esta oferta")


class CVGenerator:
    """
    Generates optimized CV PDFs by compiling LaTeX templates.
    """

    @staticmethod
    def escape_latex(text: str) -> str:
        """
        Escapa caracteres especiales de LaTeX en texto plano.
        No debe aplicarse a bloques LaTeX ya generados.
        """
        if not isinstance(text, str):
            return str(text)
        replacements = [
            ('\\', r'\textbackslash{}'),
            ('&',  r'\&'),
            ('%',  r'\%'),
            ('$',  r'\$'),
            ('#',  r'\#'),
            ('_',  r'\_'),
            ('{',  r'\{'),
            ('}',  r'\}'),
            ('^',  r'\textasciicircum{}'),
            ('~',  r'\textasciitilde{}'),
        ]
        for char, escaped in replacements:
            text = text.replace(char, escaped)
        return text

    @staticmethod
    async def generate_for_offer(offer_id: int) -> str:
        """
        Generates optimized CV for a job offer and uploads to Cloudinary.

        Args:
            offer_id: ID of JobOffer from database

        Returns:
            URL of generated PDF in Cloudinary

        Raises:
            ValueError: If offer not found, PDF generation fails, etc.
        """
        async with AsyncSessionLocal() as session:
            # Fetch offer + user data
            stmt = select(JobOffer).where(JobOffer.id == offer_id)
            result = await session.execute(stmt)
            offer = result.scalar_one_or_none()

            if not offer:
                raise ValueError(f"Offer {offer_id} not found")

            # Update status to "processing"
            offer.status = "processing"
            await session.commit()

            # Fetch user
            stmt = select(User).where(User.id == offer.user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                raise ValueError(f"User {offer.user_id} not found")

        try:
            # Generate LaTeX-based CV with offer context
            pdf_path = await CVGenerator._compile_latex(
                offer=offer,
                user=user
            )

            # Upload to Cloudinary
            cv_url = upload_pdf(
                file_path=pdf_path,
                public_id=f"cv_optimizados/offer_{offer_id}_cv"
            )

            # Update database with URL and mark as done
            async with AsyncSessionLocal() as session:
                stmt = select(JobOffer).where(JobOffer.id == offer_id)
                result = await session.execute(stmt)
                offer = result.scalar_one()
                offer.optimized_cv_url = cv_url
                offer.status = "done"
                await session.commit()

            # Cleanup temp file
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

            return cv_url

        except Exception as e:
            # Mark as error in database
            async with AsyncSessionLocal() as session:
                stmt = select(JobOffer).where(JobOffer.id == offer_id)
                result = await session.execute(stmt)
                offer = result.scalar_one()
                offer.status = "error"
                await session.commit()
            raise

    @staticmethod
    async def _adapt_with_deepseek(offer_text: str, master_data: dict) -> "AdaptedCVSections":
        """
        Adapta las secciones del CV a una oferta específica usando DeepSeek.

        Args:
            offer_text: Texto completo de la oferta de trabajo
            master_data: Datos maestros del CV del usuario

        Returns:
            AdaptedCVSections con resumen, habilidades y experiencia adaptados
        """
        llm = ChatOpenAI(
            api_key=os.environ.get("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
            model="deepseek-chat",
            temperature=0.3
        )
        parser = JsonOutputParser(pydantic_object=AdaptedCVSections)

        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "Eres experto en optimización de CVs para ATS y reclutadores técnicos.\n"
             "Adapta las secciones del CV a la oferta SIN inventar experiencia inexistente.\n"
             "Reordena y enfatiza habilidades relevantes. Integra keywords de la oferta de forma natural.\n"
             "Idioma: español. LaTeX válido en habilidades y experiencia.\n"
             "{format_instructions}"),
            ("human", "PERFIL BASE:\n{master_data}\n\nOFERTA:\n{offer_text}")
        ])

        chain = prompt | llm | parser

        return await chain.ainvoke({
            "master_data": json.dumps(master_data, ensure_ascii=False, indent=2),
            "offer_text": offer_text,
            "format_instructions": parser.get_format_instructions()
        })

    @staticmethod
    async def _compile_latex(offer: JobOffer, user: User) -> str:
        """
        Compiles LaTeX template to PDF.

        Returns:
            Path to generated PDF file
        """
        # Cargar datos maestros del CV
        try:
            with open("data/cv_master_data.json", encoding="utf-8") as f:
                master_data = json.load(f)
        except FileNotFoundError:
            print("[WARN] cv_master_data.json not found, using empty master_data")
            master_data = {}

        # Adaptar secciones con DeepSeek si hay texto de oferta disponible
        adapted = None
        if offer.raw_text:
            try:
                print("[INFO] Adaptando CV con DeepSeek...")
                adapted = await CVGenerator._adapt_with_deepseek(offer.raw_text, master_data)
                print("[OK] Adaptación completada")
            except Exception as e:
                print(f"[WARN] DeepSeek adaptation failed, usando plantilla base: {e}")

        # Create temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            latex_file = Path(tmpdir) / "cv.tex"
            pdf_file = Path(tmpdir) / "cv.pdf"

            # Generate LaTeX content
            latex_content = CVGenerator._build_latex_template(offer, user, master_data, adapted)

            # Write LaTeX file
            latex_file.write_text(latex_content, encoding='utf-8')

            # Compile to PDF using pdflatex (async, 2 passes for cross-references)
            pdflatex_cmd = [
                "pdflatex",
                "-interaction=nonstopmode",
                "-output-directory", str(tmpdir),
                str(latex_file)
            ]

            for pass_num in (1, 2):
                proc = await asyncio.create_subprocess_exec(
                    *pdflatex_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()

                if proc.returncode != 0:
                    raise RuntimeError(
                        f"LaTeX compilation failed (pass {pass_num}):\n{stderr.decode(errors='replace')}"
                    )

            if not pdf_file.exists():
                raise RuntimeError("PDF file not generated by pdflatex")

            # Copy to persistent location before tmpdir cleanup
            final_path = Path("data") / f"cv_offer_{offer.id}.pdf"
            final_path.parent.mkdir(parents=True, exist_ok=True)

            with open(pdf_file, 'rb') as src:
                with open(final_path, 'wb') as dst:
                    dst.write(src.read())

            return str(final_path)

    @staticmethod
    def _build_latex_template(offer: JobOffer, user: User, master_data: dict = None, adapted: "AdaptedCVSections" = None) -> str:
        """
        Builds LaTeX CV template optimized for the job offer.

        Combines data from:
        - master_data: CV base del usuario
        - adapted: Secciones adaptadas por DeepSeek a la oferta
        - cv_template.tex: Plantilla personalizada con placeholders

        Args:
            offer: JobOffer del usuario
            user: User del usuario
            master_data: Datos maestros del CV
            adapted: Secciones adaptadas por IA (optional)

        Returns:
            LaTeX content ready to compile
        """
        if master_data is None:
            master_data = {}

        # Intentar cargar plantilla personalizada
        try:
            with open("data/cv_template.tex", encoding="utf-8") as f:
                template = f.read()
        except FileNotFoundError:
            print("[WARN] cv_template.tex not found, using hardcoded fallback")
            template = CVGenerator._get_fallback_template()

        # --- Preparar sustituciones ---
        replacements = {}

        # Datos personales
        replacements["{{NOMBRE}}"] = CVGenerator.escape_latex(master_data.get("nombre", "Tu Nombre"))
        replacements["{{EMAIL}}"] = CVGenerator.escape_latex(master_data.get("email", "tu@email.com"))
        replacements["{{LINKEDIN}}"] = CVGenerator.escape_latex(master_data.get("linkedin", "tu-perfil"))
        replacements["{{GITHUB}}"] = CVGenerator.escape_latex(master_data.get("github", "tu-usuario"))

        # Resumen: usar adaptado si disponible, sino base
        if adapted:
            replacements["{{RESUMEN}}"] = adapted.resumen
        else:
            replacements["{{RESUMEN}}"] = CVGenerator.escape_latex(master_data.get("resumen_base", "Profesional con experiencia en desarrollo."))

        # Habilidades: usar adaptadas si disponible, sino base
        if adapted:
            replacements["{{HABILIDADES}}"] = adapted.habilidades
        else:
            habilidades_base = master_data.get("habilidades_base", {})
            skills_text = CVGenerator._format_skills_latex(habilidades_base)
            replacements["{{HABILIDADES}}"] = skills_text

        # Experiencia: usar adaptada si disponible, sino base
        if adapted:
            replacements["{{EXPERIENCIA}}"] = adapted.experiencia
        else:
            exp_base = master_data.get("experiencia_base", [])
            exp_text = CVGenerator._format_experience_latex(exp_base)
            replacements["{{EXPERIENCIA}}"] = exp_text

        # Formación
        formacion = master_data.get("formacion", [])
        formacion_text = CVGenerator._format_education_latex(formacion)
        replacements["{{FORMACION}}"] = formacion_text

        # Proyectos
        proyectos = master_data.get("proyectos", [])
        proyectos_text = CVGenerator._format_projects_latex(proyectos)
        replacements["{{PROYECTOS}}"] = proyectos_text

        # Realizar sustituciones
        result = template
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)

        return result

    @staticmethod
    def _format_skills_latex(habilidades_base: dict) -> str:
        """Formatea habilidades en LaTeX itemize."""
        if not habilidades_base:
            return r"\begin{itemize}\item Habilidades técnicas\end{itemize}"

        text = r"\begin{itemize}" + "\n"
        for categoria, items in habilidades_base.items():
            if isinstance(items, list):
                for item in items:
                    text += f"  \\item {item}\n"
            else:
                text += f"  \\item {items}\n"
        text += r"\end{itemize}"
        return text

    @staticmethod
    def _format_experience_latex(experiencia_base: list) -> str:
        """Formatea experiencia en LaTeX."""
        if not experiencia_base:
            return "Experiencia profesional disponible bajo consulta."

        text = ""
        for exp in experiencia_base:
            titulo = exp.get("titulo", "Posición")
            empresa = exp.get("empresa", "Empresa")
            periodo = exp.get("periodo", "Período")
            descripcion = exp.get("descripcion", "")
            text += f"\\textbf{{{titulo}}} --- {empresa} ({periodo})\\\\\n"
            if descripcion:
                text += f"{descripcion}\\\\\n"
            text += "\n"
        return text

    @staticmethod
    def _format_education_latex(formacion: list) -> str:
        """Formatea educación en LaTeX."""
        if not formacion:
            return "Formación profesional disponible bajo consulta."

        text = ""
        for edu in formacion:
            titulo = edu.get("titulo", "Formación")
            centro = edu.get("centro", "Centro")
            anio = edu.get("anio", "Año")
            text += f"\\textbf{{{titulo}}} --- {centro} ({anio})\\\\\n"
        return text

    @staticmethod
    def _format_projects_latex(proyectos: list) -> str:
        """Formatea proyectos en LaTeX itemize."""
        if not proyectos:
            return r"\begin{itemize}\item Proyectos destacados disponibles\end{itemize}"

        text = r"\begin{itemize}" + "\n"
        for proj in proyectos:
            nombre = proj.get("nombre", "Proyecto")
            descripcion = proj.get("descripcion", "")
            techs = ", ".join(proj.get("tecnologias", []))
            text += f"  \\item \\textbf{{{nombre}}}: {descripcion}"
            if techs:
                text += f" ({techs})"
            text += "\n"
        text += r"\end{itemize}"
        return text

    @staticmethod
    def _get_fallback_template() -> str:
        """Plantilla hardcodeada como fallback."""
        return r"""
\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[spanish]{babel}
\usepackage[margin=0.75in]{geometry}
\usepackage{hyperref}

\pagestyle{empty}

\begin{document}

\begin{center}
{\Large \textbf{{{NOMBRE}}}}\\
{{EMAIL}} $|$ \href{https://linkedin.com/in/{{LINKEDIN}}}{LinkedIn} $|$ \href{https://github.com/{{GITHUB}}}{GitHub}
\end{center}

\hrule\vspace{10pt}

\section*{Resumen}
{{RESUMEN}}

\section*{Habilidades Técnicas}
{{HABILIDADES}}

\section*{Experiencia}
{{EXPERIENCIA}}

\section*{Formación}
{{FORMACION}}

\section*{Proyectos}
{{PROYECTOS}}

\vspace{10pt}
\hrule

\footnotesize{\textit{Documento generado automáticamente por OptiCV Engine}}

\end{document}
"""
