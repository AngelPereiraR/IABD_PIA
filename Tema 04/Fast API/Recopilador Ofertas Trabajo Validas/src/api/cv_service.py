import os
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import cloudinary
import cloudinary.uploader
import uuid
import asyncio
import json

from src.database import User
from pydantic import BaseModel as PydanticModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.loader import load_cv_context

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", ""),
    api_key=os.getenv("CLOUDINARY_API_KEY", ""),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", ""),
)


# --- PYDANTIC MODELS ---
class CVFormacion(PydanticModel):
    titulo: str = Field(description="Título de la formación")
    centro: str = Field(description="Centro educativo")
    anio: str = Field(description="Año de finalización")


class CVExperiencia(PydanticModel):
    puesto: str = Field(description="Título del puesto")
    empresa: str = Field(description="Nombre de la empresa")
    duracion: str = Field(description="Período de trabajo")
    logros: list[str] = Field(description="Logros o responsabilidades en el puesto")
    impacto: Optional[str] = Field(default=None, description="Impacto cuantificable (ej: 'Redujo tiempo de despliegue un 40%')")


class CVProyecto(PydanticModel):
    nombre: str = Field(description="Nombre del proyecto")
    descripcion: str = Field(description="Descripción breve del proyecto")
    tecnologias: list[str] = Field(description="Tecnologías utilizadas")


class CVIdioma(PydanticModel):
    idioma: str = Field(description="Nombre del idioma")
    nivel: str = Field(description="Nivel de dominio (nativo, fluido, intermedio, básico)")


class CVCertificacion(PydanticModel):
    nombre: str = Field(description="Nombre de la certificación")
    emisor: str = Field(description="Entidad emisora")
    anio: str = Field(description="Año de obtención")


class CVCurso(PydanticModel):
    nombre: str = Field(description="Nombre del curso")
    plataforma: str = Field(description="Plataforma (Coursera, Udemy, etc.)")
    anio: str = Field(description="Año de realización")


class CVVoluntariado(PydanticModel):
    organizacion: str = Field(description="Nombre de la organización")
    rol: str = Field(description="Rol desempeñado")
    descripcion: str = Field(description="Descripción de actividades")
    anio: str = Field(description="Año de participación")


class CVMasterData(PydanticModel):
    """Modelo de datos maestros del CV extraídos del PDF"""
    nombre: str = Field(description="Nombre completo")
    email: str = Field(description="Email de contacto")
    linkedin: Optional[str] = Field(default=None, description="Perfil de LinkedIn (usuario)")
    github: Optional[str] = Field(default=None, description="Usuario de GitHub")
    telefono: Optional[str] = Field(default=None, description="Teléfono de contacto")
    ubicacion: Optional[str] = Field(default=None, description="Ubicación/Ciudad")
    web: Optional[str] = Field(default=None, description="Website o portfolio personal")
    resumen_base: str = Field(description="Resumen profesional")
    formacion: list[CVFormacion] = Field(description="Formación académica")
    experiencia_base: list[CVExperiencia] = Field(description="Experiencia laboral")
    proyectos: list[CVProyecto] = Field(description="Proyectos destacados")
    habilidades_base: dict[str, list[str]] = Field(description="Habilidades por categoría")
    idiomas: list[CVIdioma] = Field(default=[], description="Idiomas hablados")
    certificaciones: list[CVCertificacion] = Field(default=[], description="Certificaciones profesionales")
    cursos: list[CVCurso] = Field(default=[], description="Cursos realizados")
    voluntariado: list[CVVoluntariado] = Field(default=[], description="Experiencia de voluntariado")


class CVService:
    @staticmethod
    async def extract_cv_data(pdf_text: str) -> dict:
        """
        Extrae datos estructurados del texto del CV usando DeepSeek.

        Args:
            pdf_text: Texto extraído del PDF del CV

        Returns:
            Dict con los datos estructurados (nombre, email, formacion, etc.)

        Raises:
            Exception: Si DeepSeek falla o no puede extraer los datos
        """
        llm = ChatOpenAI(
            api_key=os.environ.get("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
            model="deepseek-chat",
            temperature=0.2
        )
        parser = JsonOutputParser(pydantic_object=CVMasterData)

        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "Eres experto en extracción de datos de CVs en PDF.\n"
             "Extrae SOLO información EXISTENTE en el CV. NUNCA inventes datos.\n\n"
             "CAMPOS REQUERIDOS:\n"
             "- nombre: Nombre completo del candidato\n"
             "- email: Email de contacto\n"
             "- resumen_base: Resumen o perfil profesional (máx 3-4 líneas)\n"
             "- formacion: Array de estudios [titulo, centro, anio]\n"
             "- experiencia_base: Array de trabajos [puesto, empresa, duracion, logros (array), impacto (métrica cuantificable si existe)]\n"
             "- proyectos: Array [nombre, descripcion, tecnologias (array)]\n"
             "- habilidades_base: Dict con categorías => array de skills\n\n"
             "CAMPOS OPCIONALES (null/[] si no existen en el CV):\n"
             "- linkedin: Usuario de LinkedIn (solo username)\n"
             "- github: Usuario de GitHub\n"
             "- telefono: Teléfono de contacto\n"
             "- ubicacion: Ciudad/País\n"
             "- web: Website personal o portfolio\n"
             "- idiomas: Array [idioma, nivel(nativo/fluido/intermedio/básico)]\n"
             "- certificaciones: Array [nombre, emisor, anio]\n"
             "- cursos: Array [nombre, plataforma, anio]\n"
             "- voluntariado: Array [organizacion, rol, descripcion, anio]\n\n"
             "⚠️ CRÍTICO: Si un campo opcional NO aparece en el CV, devuelve null (no string vacío) o [] para arrays.\n"
             "NO INVENTAR NUNCA datos. impacto solo si hay métrica explícita en el CV.\n"
             "{format_instructions}"),
            ("human", "Extrae los datos del siguiente CV:\n\n{cv_text}")
        ])

        chain = prompt | llm | parser

        print("[INFO] Extrayendo datos del CV con DeepSeek...")
        try:
            result = await chain.ainvoke({
                "cv_text": pdf_text,
                "format_instructions": parser.get_format_instructions()
            })
            print("[OK] Datos extraídos correctamente")
            return result
        except Exception as e:
            print(f"[WARN] Error extrayendo datos con DeepSeek: {e}")
            raise ValueError(f"Failed to extract CV data: {str(e)}")

    @staticmethod
    async def upload_cv(
        db: AsyncSession,
        user_id: uuid.UUID,
        file_path: str,
    ) -> dict:
        """
        Upload CV to Cloudinary, extract structured data, and save to user.cv_data
        """
        try:
            # 1. Upload to Cloudinary
            print("[INFO] Uploading CV to Cloudinary...")
            response = await asyncio.to_thread(
                cloudinary.uploader.upload,
                file_path,
                resource_type="auto",
                overwrite=True,
                folder="opticv/cv",
                public_id=f"{user_id}_{uuid.uuid4()}",
            )
            file_url = response.get("secure_url")
            print(f"[OK] CV uploaded: {file_url}")

            # 2. Extract text from PDF
            print("[INFO] Extracting text from PDF...")
            pdf_text = await asyncio.to_thread(load_cv_context, file_path)
            if not pdf_text:
                print("[WARN] PDF appears to be empty or unreadable")
                pdf_text = ""

            # 3. Extract structured data with DeepSeek (if PDF has content)
            cv_data = None
            if pdf_text:
                try:
                    extracted = await CVService.extract_cv_data(pdf_text)
                    cv_data = extracted
                    print(f"[OK] CV data extracted: nombre={extracted.get('nombre', '?')}")
                except Exception as e:
                    print(f"[WARN] Failed to extract CV data, continuing without it: {e}")

            # 4. Update user's CV info in database
            print("[INFO] Updating user record...")
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if user:
                user.master_cv_url = file_url
                if cv_data:
                    # Convert extracted data to dict for JSONB storage
                    user.cv_data = cv_data if isinstance(cv_data, dict) else cv_data.model_dump()
                await db.commit()
                await db.refresh(user)
                print("[OK] User record updated")

            return {
                "cv_url": file_url,
                "user_id": str(user_id),
                "file_path": file_path,
            }
        except Exception as e:
            print(f"[ERROR] CV upload failed: {e}")
            raise Exception(f"Error uploading CV to Cloudinary: {str(e)}")

    @staticmethod
    async def get_current_cv(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> Optional[str]:
        """Get user's current CV URL"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user:
            return user.master_cv_url
        return None

    @staticmethod
    async def delete_cv(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> bool:
        """Remove CV from user profile"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user:
            user.master_cv_url = None
            await db.commit()
            return True
        return False
