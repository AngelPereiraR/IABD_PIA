import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

load_dotenv()

# Definimos la estructura exacta que queremos que devuelva la IA
class RecruitmentDecision(BaseModel):
    match: bool = Field(description="True si supera AMBAS fases (ATS + Humano), False si cae en alguna.")
    match_score: int = Field(description="0-59 (Fallo ATS), 60-69 (Fallo Humano), 70-89 (Apto), 90+ (Top).")
    job_title: str = Field(description="El título del puesto normalizado extraído de la oferta.")
    company: str = Field(description="Nombre de la empresa.")
    salary: str = Field(description="Rango salarial detectado o 'No especificado'.")
    posted_date: str = Field(description="Fecha de publicación o antigüedad extraída LITERALMENTE del texto (ej. 'Hace 2 días', 'Posted 3 hours ago').")
    benefits: str = Field(description="Beneficios clave detectados.")
    summary: str = Field(description="Justificación. Si falla en Fase 1: Tono ROBOTICO/ERROR. Si llega a Fase 2: Tono PROFESIONAL/RRHH.")

class RecruitmentBrain:
    """
    Clase que encapsula la lógica de decisión usando LLMs (DeepSeek).
    """
    def __init__(self):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("Faltan credenciales de DeepSeek (DEEPSEEK_API_KEY) en .env")

        # Configuración del modelo DeepSeek (API compatible con OpenAI)
        # Usamos temperature=0 para máxima precisión y determinismo
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            temperature=0,
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

        # Configurar el parser de salida JSON
        self.parser = JsonOutputParser(pydantic_object=RecruitmentDecision)

        # Crear el Template del Prompt
        self.prompt = PromptTemplate(
            template="""
            Eres un Analista de Talento Experto y Universal.
            
            ⚠️ **INSTRUCCIONES DE GROUNDING (ANTI-ALUCINACION):**
            1. Tu analisis debe basarse **UNICA Y EXCLUSIVAMENTE** en el contenido de "TEXTO DE LA WEB".
            2. **PROHIBIDO** usar conocimiento externo o suposiciones no presentes en el texto.
            3. Debes extraer la fecha de publicacion real del texto para verificar su vigencia.
            
            DATOS DEL CANDIDATO (CV):
            ----------------------------------------
            {cv_context}
            ----------------------------------------
            
            TEXTO DE LA WEB (JD - INFORMACION FRESCA):
            ----------------------------------------
            {offer_markdown}
            ----------------------------------------
            
            INSTRUCCIONES DE PROCESAMIENTO:

            --- ETAPA 0: VALIDACIÓN DE ESTADO (CRÍTICO - EJECUTAR PRIMERO) ---
            Antes de leer cualquier requisito, busca **LITERALMENTE** estas frases o indicadores de que la oferta NO es válida.
            
            1. **INDICADORES DE CIERRE:**
               - "No longer accepting applications"
               - "This job is no longer active"
               - "Job closed"
               - "Ya no se aceptan solicitudes"
               - "Esta oferta de empleo ha expirado"
               - "Oferta cerrada"
               - "Dejó de admitir solicitudes"
               - "No admite más candidatos"
            
            2. **EXCEPCIONES (FALSOS POSITIVOS - NO DESCARTAR):**
               Si encuentras estas frases, la oferta ESTÁ ACTIVA (solicitud externa):
               - "Apply on company website" / "Solicitar en el sitio web de la empresa"
               - "You will be redirected to..."
               - "Start your application on..."
               - "See full details on..."
               - "Solicitar"
               - Cualquier indicación de proceso en Workday, Greenhouse, Lever, etc.
               -> **EN ESTOS CASOS: CONTINÚA EL ANÁLISIS NORMALMENTE.**

            3. **INDICADORES DE ERROR / PÁGINA GENÉRICA:**
               - Si el texto parece ser una página de Login ("Sign in", "Join now").
               - Si el texto es una lista de empleos genérica ("Jobs in Madrid", "Similar jobs") y no la descripción de UN puesto concreto.
               - Si el texto es muy corto (<200 caracteres) o irrelevante.

            > **SI ENCUENTRAS ALGUNO DE ESTOS INDICADORES:**
            - **DETÉN EL ANÁLISIS INMEDIATAMENTE.**
            - **Score: 0.**
            - **Match: False.**
            - **Summary:** "SYSTEM_BLOCK: OFERTA CERRADA O NO DISPONIBLE."

            --- ETAPA 1: CALIBRACION Y FILTRO ATS (Solo si pasa Etapa 0) ---
            
            PASO A: DETECCION DE CONTEXTO
            1. Identifica el **Sector** de la oferta (ej. Sanidad, Ventas, IT).
            2. Identifica el **Nivel Requerido** (Becario, Junior, Mid, Senior, Manager).
            3. **FECHA:** Extrae 'posted_date'.
            
            PASO B: KILLER QUESTIONS (FILTROS ELIMINATORIOS)
            1. **UBICACION:** Si es Presencial/Hibrido y la provincia no coincide (y no hay disponibilidad de traslado) -> FALLO.
            2. **EXPERIENCIA (CRÍTICO):** - Extrae los años de experiencia solicitados en la descripción (ej. "3 años", "+5 años").
               - Compara con la experiencia TOTAL del candidato en ese rol/tecnología.
               - **REGLA ESTRICTA:** Si Exp_Candidato < Exp_Requerida -> FALLO AUTOMÁTICO. 
               - No redondees hacia arriba. 2.5 años NO son 3 años para este filtro.
            3. **HARD SKILLS:** Si falta alguna skill marcada como "Imprescindible/Must" -> FALLO.
            4. **IDIOMAS:** Si es requisito excluyente -> FALLO.

            > **SI FALLA LA ETAPA 1:**
            - Score: 0-59. Match: False. Summary: "ATS_BLOCK: [MOTIVO EXACTO, ej. Experiencia Insuficiente (Tiene 2, Piden 3)]".

            --- ETAPA 2: EVALUACION CUALITATIVA ---
            1. **Coherencia:** ¿Tiene sentido este puesto para su trayectoria?
            2. **Profundidad:** Valora logros tangibles vs requisitos.
            
            SISTEMA DE PUNTUACION FASE 2:
            - **60-69 (Descarte):** Valido pero debil. Match: False.
            - **70-79 (Apto):** Cumple. Match: True.
            - **80-89 (Fuerte):** Destaca. Match: True.
            - **90-100 (Ideal):** Perfecto. Match: True.

            EXTRACCION DE DATOS:
            - Salary, Benefits y Posted Date.

            FORMATO DE SALIDA JSON:
            {format_instructions}
            """,
            input_variables=["cv_context", "offer_markdown"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )

        # Crear la cadena (Chain) de procesamiento
        self.chain = self.prompt | self.llm | self.parser

    def analyze_offer(self, cv_text: str, offer_markdown: str) -> dict:
        """
        Analiza una oferta frente al CV y devuelve una decisión estructurada.
        """
        try:
            print("DeepSeek está analizando la oferta...")
            
            # Ejecutar la cadena
            result = self.chain.invoke({
                "cv_context": cv_text,
                "offer_markdown": offer_markdown
            })
            
            # Validación extra: asegurar que match es booleano
            if not isinstance(result.get("match"), bool):
                # Fallback simple por si el modelo devuelve string "true"
                result["match"] = str(result.get("match")).lower() == "true"
                
            return result

        except Exception as e:
            print(f"Error en el análisis de DeepSeek: {e}")
            # Devolver un fallo seguro para no romper el bucle
            return {
                "match": False, 
                "job_title": "Error Análisis", 
                "company": "N/A", 
                "summary": "Falló el procesamiento del LLM."
            }

if __name__ == "__main__":
    # --- PRUEBA UNITARIA ---
    print("🧪 Iniciando prueba del Cerebro (DeepSeek)...")
    
    # 1. Mock de CV (Simulando lo que vendría de loader.py)
    mock_cv = """
    Perfil: Desarrollador Python Junior
    Habilidades: Python, Django, FastAPI, LangChain, AWS, Docker.
    Experiencia: 1 año creando APIs y bots.
    Idiomas: Español (Nativo), Inglés (B2).
    """
    
    # 2. Mock de Oferta (Simulando lo que vendría de scraper.py)
    # Caso A: Oferta que DEBERÍA encajar
    good_offer = """
    # Junior Backend Engineer
    ## Tech Corp
    Buscamos un desarrollador con experiencia sólida en Python y frameworks modernos como FastAPI.
    Valorable experiencia en IA Generativa y LangChain.
    Trabajo remoto.
    """
    
    # Caso B: Oferta que NO debería encajar
    bad_offer = """
    # Chef de Cocina
    ## Restaurante El Gusto
    Buscamos cocinero experto en paellas y comida mediterránea.
    """

    try:
        brain = RecruitmentBrain()
        
        print("\n--- TEST 1: Oferta Compatible ---")
        decision1 = brain.analyze_offer(mock_cv, good_offer)
        print(json.dumps(decision1, indent=2, ensure_ascii=False))
        
        print("\n--- TEST 2: Oferta Incompatible ---")
        decision2 = brain.analyze_offer(mock_cv, bad_offer)
        print(json.dumps(decision2, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"\nError: {e}")
        print("PISTA: Verifica tu DEEPSEEK_API_KEY en el .env")