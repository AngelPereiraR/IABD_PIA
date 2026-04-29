"""
CV Generator Module - Generates optimized CVs from job offer context.

Combines LaTeX templates with DeepSeek analysis to create personalized PDFs.
Uploads to Cloudinary for persistent storage.
"""
import os
import json
import tempfile
import asyncio
import urllib.request
import unicodedata
import re
from pathlib import Path
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel as PydanticModel, Field

from src.storage import upload_pdf_async
from src.database import AsyncSessionLocal, JobOffer, User
from src.latex_compiler import compile_latex
from sqlalchemy import select


class AdaptedCVSections(PydanticModel):
    """Modelo de secciones CV adaptadas por DeepSeek a una oferta específica."""
    resumen: str = Field(description="Párrafo resumen adaptado a la oferta (2-3 frases, verbos de acción, sin LaTeX)")
    habilidades: list[str] = Field(description="Lista de habilidades/skills relevantes para esta oferta (máx 5-8, sin LaTeX)")
    experiencia: list[str] = Field(description="Logros relevantes con formato [EXP0] logro1, [EXP1] logro2. Índice EXP indica posición en experiencia_base.")
    keywords_ats: list[str] = Field(description="5-8 palabras clave técnicas CLAVE de la oferta")


class CVGenerator:
    """
    Generates optimized CV PDFs by compiling LaTeX templates.
    """

    @staticmethod
    def normalize_filename(text: str) -> str:
        """
        Normaliza un texto para usar como nombre de archivo.
        Elimina tildes, espacios, caracteres especiales.
        Ej: "Ángel Pereira" -> "Angel_Pereira"
        """
        if not text:
            return ""
        # Eliminar tildes y acentos
        nfkd = unicodedata.normalize('NFKD', text)
        normalized = ''.join([c for c in nfkd if not unicodedata.combining(c)])
        # Reemplazar espacios y caracteres especiales por guiones bajos
        normalized = re.sub(r'[^a-zA-Z0-9]+', '_', normalized)
        # Eliminar guiones bajos al inicio y final
        normalized = normalized.strip('_')
        return normalized

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
    async def generate_for_offer(offer_id: int, db=None) -> str:
        """
        Generates optimized CV for a job offer and uploads to Cloudinary.

        Args:
            offer_id: ID of JobOffer from database
            db: AsyncSession from FastAPI dependency (avoids event loop conflicts)

        Returns:
            URL of generated PDF in Cloudinary

        Raises:
            ValueError: If offer not found, PDF generation fails, etc.
        """
        # Use passed db session or create new one if not provided
        if db is not None:
            # Use existing session (from FastAPI endpoint)
            stmt = select(JobOffer).where(JobOffer.id == offer_id)
            result = await db.execute(stmt)
            offer = result.scalar_one_or_none()

            if not offer:
                raise ValueError(f"Offer {offer_id} not found")

            # Update status to "processing"
            offer.status = "processing"
            await db.commit()

            # Fetch user
            stmt = select(User).where(User.id == offer.user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                raise ValueError(f"User {offer.user_id} not found")
        else:
            # Create new session only if not provided
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

            # Generate normalized filename: Puesto_Empresa_Nombre_Candidato
            job_title_normalized = CVGenerator.normalize_filename(offer.job_title or "Oferta")
            company_normalized = CVGenerator.normalize_filename(offer.company or "Empresa")
            candidate_name_normalized = CVGenerator.normalize_filename(
                user.cv_data.get("nombre") if user.cv_data and isinstance(user.cv_data, dict) else user.email.split("@")[0]
            )
            normalized_filename = f"{job_title_normalized}_{company_normalized}_{candidate_name_normalized}"

            # Upload to Cloudinary
            cv_url = await upload_pdf_async(
                file_path=pdf_path,
                public_id=f"cv_optimizados/{normalized_filename}"
            )

            # Update database with URL and mark as done
            if db is not None:
                # Use existing session
                stmt = select(JobOffer).where(JobOffer.id == offer_id)
                result = await db.execute(stmt)
                offer_updated = result.scalar_one()
                offer_updated.optimized_cv_url = cv_url
                offer_updated.status = "done"
                await db.commit()
            else:
                # Create new session
                async with AsyncSessionLocal() as session:
                    stmt = select(JobOffer).where(JobOffer.id == offer_id)
                    result = await session.execute(stmt)
                    offer_updated = result.scalar_one()
                    offer_updated.optimized_cv_url = cv_url
                    offer_updated.status = "done"
                    await session.commit()

            return cv_url

        except Exception as e:
            # Mark as error in database
            if db is not None:
                # Use existing session
                stmt = select(JobOffer).where(JobOffer.id == offer_id)
                result = await db.execute(stmt)
                offer_err = result.scalar_one()
                offer_err.status = "error"
                await db.commit()
            else:
                # Create new session
                async with AsyncSessionLocal() as session:
                    stmt = select(JobOffer).where(JobOffer.id == offer_id)
                    result = await session.execute(stmt)
                    offer_err = result.scalar_one()
                    offer_err.status = "error"
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
            model="deepseek-v4-flash",
            temperature=0
        )
        parser = JsonOutputParser(pydantic_object=AdaptedCVSections)

        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "Eres experto en filtrar CVs para ofertas específicas.\n"
             "REGLA: Solo usa datos que EXISTEN en el perfil base. NO inventar nunca.\n"
             "PERO: Sí debes FILTRAR - incluir SOLO lo relevante para esta oferta.\n\n"
             "DETECCIÓN Y NORMALIZACIÓN DE IDIOMA:\n"
             "1. PRIMERO: Detecta el idioma PRINCIPAL del perfil base (master_data).\n"
             "2. LUEGO: Genera TODO el contenido adaptado en ESE MISMO IDIOMA.\n"
             "3. Esto incluye TODAS las secciones: resumen, habilidades, experiencia, idiomas, etc.\n"
             "4. Ejemplo:\n"
             "   - Si master_data está en ESPAÑOL → devuelve TODA la adaptación en ESPAÑOL\n"
             "   - Si master_data está en INGLÉS → devuelve TODA la adaptación en INGLÉS\n"
             "5. Para idiomas en la sección: mantén los nombres de idiomas en el mismo idioma del CV.\n"
             "   Ej: Si CV en español, devuelve 'Inglés', 'Francés', etc.\n"
             "       Si CV en inglés, devuelve 'Spanish', 'French', etc.\n\n"
             "CAMPOS A GENERAR:\n"
             "- resumen: 2-3 frases. Reescribe el resumen_base integrando keywords de la oferta.\n"
             "  ▪ Usa contenido REAL del base, no inventes skills nuevas.\n"
             "  ▪ Ej: Base dice 'Python, FastAPI'. Oferta pide 'Python, FastAPI, Docker'.\n"
             "    → Enfatiza Python/FastAPI, omite Docker (no está en base).\n\n"
             "- habilidades: FILTRA solo las RELEVANTES para la oferta.\n"
             "  ▪ Búscalas en habilidades_base (todos los items están permitidos pero filtra).\n"
             "  ▪ Si la oferta pide Python, FastAPI, Docker, PostgreSQL:\n"
             "    - Incluye Python, FastAPI, PostgreSQL si existen en base\n"
             "    - OMITE Docker si no está en habilidades_base\n"
             "  ▪ Máximo 5-12 items. Si tienes 20, devuelve solo las 5-12 más relevantes.\n\n"
             "- experiencia: Lista de logros CON ETIQUETAS de experiencia: [\"[EXP0] logro1\", \"[EXP0] logro2\", \"[EXP1] logro3\"]\n"
             "  ▪ Prefija cada logro con [EXP0], [EXP1], [EXP2], etc indicando a qué experiencia pertenece.\n"
             "  ▪ El índice (0, 1, 2...) corresponde al orden en experiencia_base.\n"
             "  ▪ CADA logro debe tener EXACTAMENTE la etiqueta [EXPN].\n"
             "  ▪ NO DUPLICAR logros entre experiencias. Cada logro va en su experiencia.\n"
             "  ▪ SIEMPRE incluye al menos 1-2 logros totales si hay algo relevante.\n\n"
             "- formacion, certificaciones, cursos, proyectos, idiomas: FILTRA.\n"
             "  ▪ Incluye SOLO lo relevante para la oferta.\n"
             "  ▪ Si tienes 3 cursos pero solo 1 es relevante, devuelve ese 1.\n"
             "  ▪ Devuelve [] si nada es relevante.\n\n"
             "- keywords_ats: Términos CLAVE de la oferta (no del CV).\n"
             "  ▪ Extrae de offer_text. Máximo 5-8.\n\n"
             "🎯 FILOSOFÍA: Filtra para relevancia pero usa SOLO datos REALES del base.\n"
             "⚠️ IMPORTANTE: TODO el contenido generado debe estar en el idioma del perfil base (master_data).\n"
             "{format_instructions}"),
            ("human", "PERFIL BASE:\n{master_data}\n\nOFERTA:\n{offer_text}\n\nFiltra datos REALES del base. Incluye SOLO lo relevante para esta oferta. GENERA TODO EN EL IDIOMA DEL PERFIL BASE.")
        ])

        chain = prompt | llm | parser

        result = await chain.ainvoke({
            "master_data": json.dumps(master_data, ensure_ascii=False, indent=2),
            "offer_text": offer_text,
            "format_instructions": parser.get_format_instructions()
        })

        print(f"[DEBUG] DeepSeek raw result: {result}")
        print(f"[DEBUG] resumen type: {type(result.get('resumen'))}, value: {result.get('resumen')}")
        print(f"[DEBUG] habilidades type: {type(result.get('habilidades'))}, value: {result.get('habilidades')}")
        print(f"[DEBUG] experiencia type: {type(result.get('experiencia'))}, value: {result.get('experiencia')}")

        # Convert dict to AdaptedCVSections Pydantic object
        return AdaptedCVSections(**result)

    @staticmethod
    async def _compile_latex(offer: JobOffer, user: User) -> str:
        """
        Compila la plantilla LaTeX a PDF delegando en latex_compiler.

        Returns:
            Ruta al PDF generado en data/generated/
        """
        # Cargar datos maestros del CV desde user.cv_data (BD) o fallback a archivo
        master_data = {}
        if user.cv_data:
            master_data = user.cv_data if isinstance(user.cv_data, dict) else user.cv_data
            print(f"[INFO] Loaded CV data from database for user {user.email}")
        else:
            # Fallback: intentar cargar del archivo en disco
            try:
                with open("data/cv_master_data.json", encoding="utf-8") as f:
                    master_data = json.load(f)
                print("[WARN] Using fallback cv_master_data.json from disk")
            except FileNotFoundError:
                print("[WARN] cv_master_data.json not found, using empty master_data")
                master_data = {}

        # Adaptar secciones con DeepSeek si hay texto de oferta disponible
        adapted = None
        if offer.raw_text:
            try:
                print("[INFO] Adaptando CV con DeepSeek...")
                print(f"[DEBUG] master_data keys: {list(master_data.keys())}")
                print(f"[DEBUG] offer.raw_text length: {len(offer.raw_text)}")
                adapted = await CVGenerator._adapt_with_deepseek(offer.raw_text, master_data)
                print("[OK] Adaptación completada")
                print(f"[DEBUG] adapted type: {type(adapted)}, has resumen: {hasattr(adapted, 'resumen')}")
            except Exception as e:
                print(f"[WARN] DeepSeek adaptation failed, usando plantilla base: {e}")
                import traceback
                traceback.print_exc()

        # Construir contenido LaTeX
        latex_content = CVGenerator._build_latex_template(offer, user, master_data, adapted)

        # Delegar compilación al módulo especializado
        return await compile_latex(latex_content, offer.id)

    @staticmethod
    def _download_avatar(avatar_url: str) -> Optional[str]:
        """
        Downloads avatar from URL and saves to temp file.
        Returns local file path if successful, None if download fails or URL is empty.
        """
        if not avatar_url:
            return None

        try:
            # Create temporary file with image extension
            _, ext = os.path.splitext(avatar_url.split('?')[0])  # Remove query params
            if not ext:
                ext = '.jpg'

            temp_fd, temp_path = tempfile.mkstemp(suffix=ext, prefix='avatar_')
            os.close(temp_fd)  # Close file descriptor, we'll write via urllib

            print(f"[INFO] Downloading avatar from {avatar_url}...")
            urllib.request.urlretrieve(avatar_url, temp_path)
            print(f"[OK] Avatar downloaded to {temp_path}")
            return temp_path
        except Exception as e:
            print(f"[WARN] Failed to download avatar: {e}")
            return None

    @staticmethod
    def _build_latex_template(offer: JobOffer, user: User, master_data: dict = None, adapted: "AdaptedCVSections" = None) -> str:
        """
        Builds LaTeX CV template optimized for the job offer.
        IMPORTANT: Only includes REAL data from master_data. No default values.

        Combines data from:
        - master_data: CV base del usuario (datos reales)
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

        # --- Preparar sustituciones (SOLO con datos reales) ---
        replacements = {}

        # Nombre (requerido)
        if "nombre" in master_data and master_data["nombre"]:
            replacements["{{NOMBRE}}"] = CVGenerator.escape_latex(str(master_data["nombre"]))
        else:
            replacements["{{NOMBRE}}"] = ""

        # Construir línea de contacto dinámicamente: solo lo que existe
        contacto_parts = []
        if "email" in master_data and master_data["email"]:
            contacto_parts.append(CVGenerator.escape_latex(str(master_data["email"])))

        if "linkedin" in master_data and master_data["linkedin"]:
            linkedin_user = CVGenerator.escape_latex(str(master_data["linkedin"]))
            contacto_parts.append(f"\\href{{https://linkedin.com/in/{linkedin_user}}}{{linkedin.com/in/{linkedin_user}}}")

        if "github" in master_data and master_data["github"]:
            github_user = CVGenerator.escape_latex(str(master_data["github"]))
            contacto_parts.append(f"\\href{{https://github.com/{github_user}}}{{github.com/{github_user}}}")

        # Unir con separador si hay múltiples
        replacements["{{CONTACTO}}"] = "  $|$  ".join(contacto_parts) if contacto_parts else ""

        # Contacto extra (teléfono, ubicación, web) - solo si existen
        contacto_extra_parts = []
        if "telefono" in master_data and master_data["telefono"]:
            contacto_extra_parts.append(f"Tel: {CVGenerator.escape_latex(str(master_data['telefono']))}")
        if "ubicacion" in master_data and master_data["ubicacion"]:
            contacto_extra_parts.append(f"Loc: {CVGenerator.escape_latex(str(master_data['ubicacion']))}")
        if "web" in master_data and master_data["web"]:
            web_url = CVGenerator.escape_latex(str(master_data["web"]))
            contacto_extra_parts.append(f"\\href{{{web_url}}}{{{web_url}}}")

        if contacto_extra_parts:
            # Envolver cada parte en \mbox para evitar que se corte
            mboxed_parts = [f"\\mbox{{{part}}}" for part in contacto_extra_parts]
            replacements["{{CONTACTO_EXTRA}}"] = f"  $|$  {'  $|$  '.join(mboxed_parts)}"
        else:
            replacements["{{CONTACTO_EXTRA}}"] = ""

        # Foto de perfil: descargar desde avatar_url si existe
        if user and user.avatar_url:
            avatar_path = CVGenerator._download_avatar(user.avatar_url)
            if avatar_path:
                # Crear LaTeX para includegraphics con tamaño pequeño y circular
                # Escapar ruta Windows a formato LaTeX (convertir \ a /)
                latex_path = avatar_path.replace('\\', '/')
                replacements["{{FOTO}}"] = (
                    f"\\centering\n"
                    f"\\includegraphics[width=0.275\\textwidth]{{{latex_path}}}"
                )
            else:
                replacements["{{FOTO}}"] = ""
        else:
            replacements["{{FOTO}}"] = ""

        # Resumen: usar adaptado si disponible, sino base (si existe)
        resumen_content = ""
        if adapted and adapted.resumen:
            resumen_content = CVGenerator.escape_latex(adapted.resumen)
        elif "resumen_base" in master_data and master_data["resumen_base"]:
            resumen_content = CVGenerator.escape_latex(str(master_data["resumen_base"]))

        if resumen_content:
            replacements["{{RESUMEN_SECCION}}"] = (
                f"\\section*{{Resumen Profesional}}\n{resumen_content}\n\n\\vspace{{6pt}}\n"
            )
        else:
            replacements["{{RESUMEN_SECCION}}"] = ""

        # Palabras clave ATS - no mostrar sección (solo se usan internamente para adaptación)
        if adapted and adapted.keywords_ats:
            replacements["{{KEYWORDS_ATS}}"] = " ".join([CVGenerator.escape_latex(str(k)) for k in adapted.keywords_ats])
        else:
            replacements["{{KEYWORDS_ATS}}"] = ""

        # Habilidades: usar adaptadas si disponible, sino base (solo si existen)
        # Formato horizontal/inline para ahorrar espacio
        if adapted and adapted.habilidades and len(adapted.habilidades) > 0:
            # Convertir lista a formato inline (bullet separado)
            skills_text = " $\\bullet$ ".join([CVGenerator.escape_latex(str(s)) for s in adapted.habilidades])
            replacements["{{HABILIDADES}}"] = f"{{\\small {skills_text}}}"
        elif "habilidades_base" in master_data and master_data["habilidades_base"]:
            habilidades_base = master_data["habilidades_base"]
            if habilidades_base:
                skills_text = CVGenerator._format_skills_inline_latex(habilidades_base)
                replacements["{{HABILIDADES}}"] = skills_text
            else:
                replacements["{{HABILIDADES}}"] = ""
        else:
            replacements["{{HABILIDADES}}"] = ""

        # Experiencia: combinar base con logros adaptados (parseando formato [EXP0], [EXP1], etc)
        if adapted and adapted.experiencia and len(adapted.experiencia) > 0:
            exp_base = master_data.get("experiencia_base", [])
            if exp_base and len(exp_base) > 0:
                # Parsear logros adaptados y asociarlos a experiencias
                exp_text = CVGenerator._build_experience_section(exp_base, adapted.experiencia)
                replacements["{{EXPERIENCIA}}"] = exp_text
            else:
                replacements["{{EXPERIENCIA}}"] = ""
        elif "experiencia_base" in master_data and master_data["experiencia_base"]:
            exp_base = master_data["experiencia_base"]
            if exp_base:  # Solo si hay contenido
                exp_text = CVGenerator._format_experience_latex(exp_base)
                replacements["{{EXPERIENCIA}}"] = exp_text
            else:
                replacements["{{EXPERIENCIA}}"] = ""
        else:
            replacements["{{EXPERIENCIA}}"] = ""

        # Formación: solo si existe en master_data (con itemize)
        formacion = master_data.get("formacion")
        if formacion and len(formacion) > 0:
            formacion_text = CVGenerator._format_education_latex(formacion)
            if formacion_text:
                replacements["{{FORMACION}}"] = f"\\begin{{itemize}}[nosep]\n{formacion_text}\\end{{itemize}}"
            else:
                replacements["{{FORMACION}}"] = ""
        else:
            replacements["{{FORMACION}}"] = ""

        # Proyectos: solo si existe en master_data (condicional)
        proyectos = master_data.get("proyectos")
        if proyectos and len(proyectos) > 0:
            proyectos_text = CVGenerator._format_projects_latex(proyectos)
            if proyectos_text:
                replacements["{{PROYECTOS_SECCION}}"] = (
                    f"\\section*{{Proyectos Destacados}}\n{proyectos_text}\n\n\\vspace{{6pt}}\n"
                )
            else:
                replacements["{{PROYECTOS_SECCION}}"] = ""
        else:
            replacements["{{PROYECTOS_SECCION}}"] = ""

        # Certificaciones: solo si existen
        certificaciones = master_data.get("certificaciones")
        if certificaciones and len(certificaciones) > 0:
            certs_text = CVGenerator._format_certificaciones_latex(certificaciones)
            if certs_text:
                replacements["{{CERTIFICACIONES_SECCION}}"] = (
                    f"\\section*{{Certificaciones}}\n{certs_text}\n\n\\vspace{{6pt}}\n"
                )
            else:
                replacements["{{CERTIFICACIONES_SECCION}}"] = ""
        else:
            replacements["{{CERTIFICACIONES_SECCION}}"] = ""

        # Idiomas: solo si existen
        idiomas = master_data.get("idiomas")
        if idiomas and len(idiomas) > 0:
            idiomas_text = CVGenerator._format_idiomas_latex(idiomas)
            if idiomas_text:
                replacements["{{IDIOMAS_SECCION}}"] = (
                    f"\\section*{{Idiomas}}\n{idiomas_text}\n\n\\vspace{{6pt}}\n"
                )
            else:
                replacements["{{IDIOMAS_SECCION}}"] = ""
        else:
            replacements["{{IDIOMAS_SECCION}}"] = ""

        # Cursos: solo si existen
        cursos = master_data.get("cursos")
        if cursos and len(cursos) > 0:
            cursos_text = CVGenerator._format_cursos_latex(cursos)
            if cursos_text:
                replacements["{{CURSOS_SECCION}}"] = (
                    f"\\section*{{Cursos y Formación Continua}}\n{cursos_text}\n\n\\vspace{{6pt}}\n"
                )
            else:
                replacements["{{CURSOS_SECCION}}"] = ""
        else:
            replacements["{{CURSOS_SECCION}}"] = ""

        # Voluntariado: solo si es relevante para la oferta (no mostrar si no aporta)
        replacements["{{VOLUNTARIADO_SECCION}}"] = ""

        # Realizar sustituciones
        result = template
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)

        # DEBUG: Save generated LaTeX to file for inspection
        try:
            import os
            os.makedirs("data/generated", exist_ok=True)
            debug_path = f"data/generated/debug_offer_{offer.id}_template.tex"
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"[DEBUG] Generated LaTeX saved to: {debug_path}")

            # Print the content with line numbers for debugging
            lines = result.split('\n')
            print(f"[DEBUG] LaTeX template has {len(lines)} lines")
            if len(lines) >= 85:  # Print lines around line 90
                print(f"[DEBUG] Lines 80-95:")
                for i in range(max(0, 79), min(len(lines), 95)):
                    print(f"{i+1:3d}: {lines[i]}")
        except Exception as e:
            print(f"[WARN] Could not save debug LaTeX: {e}")

        return result

    @staticmethod
    def _format_skills_latex(habilidades_base: dict) -> str:
        """Formatea habilidades en LaTeX itemize. Solo si existen datos reales."""
        if not habilidades_base:
            return ""  # No values by default - only real data

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
    def _format_skills_inline_latex(habilidades_base: dict) -> str:
        """Formatea habilidades en formato inline horizontal. Solo si existen datos reales."""
        if not habilidades_base:
            return ""

        skills_list = []
        for categoria, items in habilidades_base.items():
            if isinstance(items, list):
                skills_list.extend([CVGenerator.escape_latex(str(item)) for item in items])
            else:
                skills_list.append(CVGenerator.escape_latex(str(items)))

        if not skills_list:
            return ""

        return f"{{\\small {' $\\bullet$ '.join(skills_list)}}}"

    @staticmethod
    def _format_experience_latex(experiencia_base: list) -> str:
        """Formatea experiencia en LaTeX. Solo si existen datos reales."""
        if not experiencia_base:
            return ""  # No values by default - only real data

        text = ""
        for exp in experiencia_base:
            titulo = exp.get("titulo")
            empresa = exp.get("empresa")
            periodo = exp.get("periodo")
            descripcion = exp.get("descripcion", "")
            # Only add if we have at least titulo and empresa
            if titulo and empresa:
                text += f"\\textbf{{{titulo}}} --- {empresa}"
                if periodo:
                    text += f" ({periodo})"
                text += "\\\\\n"
                if descripcion:
                    text += f"{descripcion}\\\\\n"
                text += "\n"
        return text

    @staticmethod
    def _build_experience_section(experiencia_base: list, logros_adaptados: list[str]) -> str:
        """
        Construye sección de experiencia con estructura completa (puesto, empresa, duración, logros).

        Logros adaptados deben tener formato: "[EXP0] logro1", "[EXP1] logro2"
        donde el índice indica la posición en experiencia_base.

        Args:
            experiencia_base: Lista completa de experiencias del CV base
            logros_adaptados: Lista de strings con formato "[EXPN] logro"

        Returns:
            LaTeX con puesto, empresa, duración + logros específicos para cada experiencia
        """
        import re

        if not experiencia_base:
            return ""

        # Agrupar logros por índice de experiencia
        logros_por_exp = {}
        for logro in logros_adaptados:
            # Extraer [EXP0], [EXP1], etc del inicio del logro
            match = re.match(r'\[EXP(\d+)\]\s*(.*)', logro.strip())
            if match:
                exp_idx = int(match.group(1))
                logro_limpio = match.group(2)
                if exp_idx not in logros_por_exp:
                    logros_por_exp[exp_idx] = []
                logros_por_exp[exp_idx].append(logro_limpio)
            else:
                # Si no tiene etiqueta, mostramos advertencia en debug
                print(f"[WARN] Logro sin etiqueta [EXPN]: {logro}")

        text = ""
        for idx, exp in enumerate(experiencia_base):
            puesto = exp.get("puesto")
            empresa = exp.get("empresa")
            duracion = exp.get("duracion")
            impacto = exp.get("impacto")

            if puesto and empresa:
                text += f"\\textbf{{{CVGenerator.escape_latex(str(puesto))}}} --- {CVGenerator.escape_latex(str(empresa))}"
                if duracion:
                    text += f" ({CVGenerator.escape_latex(str(duracion))})"
                text += "\n"

                # Usar SOLO los logros para ESTA experiencia
                logros_esta_exp = logros_por_exp.get(idx, [])
                if logros_esta_exp:
                    text += r"\begin{itemize}[nosep]" + "\n"
                    for logro in logros_esta_exp:
                        escaped_logro = CVGenerator.escape_latex(str(logro))
                        text += f"    \\item {escaped_logro}\n"
                    text += r"\end{itemize}"

                # Agregar impacto si existe
                if impacto:
                    text += f"\\textit{{Impacto: {CVGenerator.escape_latex(str(impacto))}}}\n"

                text += "\n"

        return text

    @staticmethod
    def _format_education_latex(formacion: list) -> str:
        """Formatea educación en LaTeX itemize. Solo si existen datos reales."""
        if not formacion:
            return ""  # No values by default - only real data

        text = ""
        for edu in formacion:
            titulo = edu.get("titulo")
            centro = edu.get("centro")
            anio = edu.get("anio")
            # Only add if we have at least titulo and centro
            if titulo and centro:
                text += f"\\item \\textbf{{{titulo}}} --- {centro}"
                if anio:
                    text += f" ({anio})"
                text += "\n"
        return text

    @staticmethod
    def _format_projects_latex(proyectos: list) -> str:
        """Formatea proyectos en LaTeX itemize. Solo si existen datos reales."""
        if not proyectos:
            return ""  # No values by default - only real data

        text = r"\begin{itemize}" + "\n"
        for proj in proyectos:
            nombre = proj.get("nombre")
            descripcion = proj.get("descripcion", "")
            techs = ", ".join(proj.get("tecnologias", []))
            # Only add if we have at least nombre
            if nombre:
                text += f"  \\item \\textbf{{{nombre}}}"
                if descripcion:
                    text += f": {descripcion}"
                if techs:
                    text += f" ({techs})"
                text += "\n"
        text += r"\end{itemize}"
        return text

    @staticmethod
    def _format_certificaciones_latex(certificaciones: list) -> str:
        """Formatea certificaciones en LaTeX. Solo si existen datos reales."""
        if not certificaciones:
            return ""

        text = r"\begin{itemize}" + "\n"
        for cert in certificaciones:
            nombre = cert.get("nombre")
            emisor = cert.get("emisor", "")
            anio = cert.get("anio", "")
            if nombre:
                text += f"  \\item \\textbf{{{nombre}}}"
                if emisor:
                    text += f" --- {emisor}"
                if anio:
                    text += f" ({anio})"
                text += "\n"
        text += r"\end{itemize}"
        return text

    @staticmethod
    def _format_idiomas_latex(idiomas: list) -> str:
        """Formatea idiomas en LaTeX. Solo si existen datos reales."""
        if not idiomas:
            return ""

        items = []
        for idioma in idiomas:
            nombre = idioma.get("idioma")
            nivel = idioma.get("nivel", "")
            if nombre:
                if nivel:
                    items.append(f"{nombre}: {nivel}")
                else:
                    items.append(nombre)

        if items:
            return "  $|$  ".join(items)
        return ""

    @staticmethod
    def _format_cursos_latex(cursos: list) -> str:
        """Formatea cursos en LaTeX. Solo si existen datos reales."""
        if not cursos:
            return ""

        text = r"\begin{itemize}" + "\n"
        for curso in cursos:
            nombre = curso.get("nombre")
            plataforma = curso.get("plataforma", "")
            anio = curso.get("anio", "")
            if nombre:
                text += f"  \\item {nombre}"
                if plataforma:
                    text += f" --- {plataforma}"
                if anio:
                    text += f" ({anio})"
                text += "\n"
        text += r"\end{itemize}"
        return text

    @staticmethod
    def _format_voluntariado_latex(voluntariado: list) -> str:
        """Formatea voluntariado en LaTeX. Solo si existen datos reales."""
        if not voluntariado:
            return ""

        text = ""
        for vol in voluntariado:
            rol = vol.get("rol")
            organizacion = vol.get("organizacion", "")
            descripcion = vol.get("descripcion", "")
            anio = vol.get("anio", "")

            if rol and organizacion:
                text += f"\\textbf{{{rol}}} --- {organizacion}"
                if anio:
                    text += f" ({anio})"
                text += "\\\\\n"
                if descripcion:
                    text += f"{descripcion}\\\\\n"
                text += "\n"

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
{{EMAIL}}  $|$\href{https://linkedin.com/in/{{LINKEDIN}}}{LinkedIn}  $|$\href{https://github.com/{{GITHUB}}}{GitHub}
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

    def generate_adapted_cv(self, original_cv: str, job_offer: str, job_title: str, company: str) -> str:
        """
        Genera HTML preview del CV adaptado a una oferta específica.

        Args:
            original_cv: Texto del CV original del usuario
            job_offer: Texto de la oferta de trabajo
            job_title: Título del puesto
            company: Nombre de la empresa

        Returns:
            HTML preview string
        """
        # Simple HTML preview - puede ser expandido con LangChain + DeepSeek si se desea
        html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }}
                h2 {{ color: #0066cc; margin-top: 20px; }}
                .job-info {{ background: #f0f0f0; padding: 10px; margin: 10px 0; }}
                .section {{ margin: 15px 0; }}
                p {{ line-height: 1.6; }}
            </style>
        </head>
        <body>
            <h1>CV Optimizado</h1>
            <div class="job-info">
                <strong>Puesto:</strong> {job_title}<br>
                <strong>Empresa:</strong> {company}
            </div>
            <h2>CV Original</h2>
            <div class="section">
                <p>{original_cv.replace(chr(10), '<br>')}</p>
            </div>
            <h2>Oferta de Trabajo</h2>
            <div class="section">
                <p>{job_offer.replace(chr(10), '<br>')}</p>
            </div>
        </body>
        </html>
        """
        return html

    def render_pdf(self, html_content: str) -> bytes:
        """
        Convierte HTML a PDF usando reportlab.

        Args:
            html_content: HTML string

        Returns:
            Bytes del PDF
        """
        from io import BytesIO
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet
        from html.parser import HTMLParser
        import re

        # Crear buffer en memoria
        pdf_buffer = BytesIO()

        # Crear documento PDF
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        # Estilos
        styles = getSampleStyleSheet()
        story = []

        # Simple parsing de HTML - extrae texto plano
        try:
            # Remove HTML tags
            text_content = re.sub('<[^<]+?>', '', html_content)
            # Decode HTML entities
            import html
            text_content = html.unescape(text_content)

            # Split en párrafos
            paragraphs = text_content.split('\n')

            for para in paragraphs:
                para = para.strip()
                if para:
                    if para.startswith('##'):
                        # Encabezado h2
                        story.append(Paragraph(para.replace('## ', '<b><font size=14>') + '</font></b>', styles['Heading2']))
                    elif para.startswith('#'):
                        # Encabezado h1
                        story.append(Paragraph(para.replace('# ', '<b><font size=16>') + '</font></b>', styles['Heading1']))
                    else:
                        # Párrafo normal
                        story.append(Paragraph(para, styles['Normal']))
                    story.append(Spacer(1, 6))
        except Exception as e:
            print(f"[WARN] Error parsing HTML for PDF: {e}")
            # Fallback: agregar texto plano
            story.append(Paragraph("Error al procesar CV adaptado", styles['Heading1']))
            story.append(Paragraph(str(e), styles['Normal']))

        # Build PDF
        doc.build(story)

        # Retornar bytes
        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()

        return pdf_bytes
