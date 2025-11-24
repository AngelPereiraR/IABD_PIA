import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

load_dotenv()

# Definimos la estructura exacta que queremos que devuelva la IA
class RecruitmentDecision(BaseModel):
    match: bool = Field(description="True si la oferta encaja con el perfil (>70%), False si no.")
    job_title: str = Field(description="El título del puesto extraído de la oferta.")
    company: str = Field(description="Nombre de la empresa ofertante.")
    summary: str = Field(description="Breve justificación de por qué encaja o no (máx 2 frases).")
    probability: float = Field(description="Probabilidad estimada de que la oferta encaje con el perfil (0 a 100) en porcentajes.")

class RecruitmentBrain:
    """
    Clase que encapsula la lógica de decisión usando LLMs (Gemma-3).
    """
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Faltan credenciales de Google (GEMINI_API_KEY) en .env")

        # Configuración del modelo Gemma-3-27b
        # Usamos temperature=0 para máxima precisión y determinismo
        self.llm = ChatGoogleGenerativeAI(
            model="gemma-3-27b-it",
            temperature=0,
            google_api_key=api_key
        )

        # Configurar el parser de salida JSON
        self.parser = JsonOutputParser(pydantic_object=RecruitmentDecision)

        # Crear el Template del Prompt
        self.prompt = PromptTemplate(
            template="""
            Actúa como un Reclutador Técnico Senior experto. Tu trabajo es filtrar ofertas de empleo para un candidato basándote en su CV.
            
            CONTEXTO DEL CANDIDATO (CV):
            ----------------------------------------
            {cv_context}
            ----------------------------------------
            
            OFERTA DE TRABAJO (Markdown Scrapeado):
            ----------------------------------------
            {offer_markdown}
            ----------------------------------------
            
            INSTRUCCIONES:
            1. Analiza los requisitos técnicos (Hard Skills) y experiencia requerida en la oferta.
            2. Compáralos con el CV del candidato.
            3. Ignora coincidencias genéricas (como "trabajo en equipo") si no hay match técnico.
            4. El umbral de aprobación es del 70% de coincidencia en requisitos obligatorios.
            5. Si falta información salarial o la empresa es confidencial, no penalices el match.
            
            FORMATO DE SALIDA:
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
            print("🧠 Gemma está analizando la oferta...")
            
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
            print(f"Error en el análisis de Gemma: {e}")
            # Devolver un fallo seguro para no romper el bucle
            return {
                "match": False, 
                "job_title": "Error Análisis", 
                "company": "N/A", 
                "summary": "Falló el procesamiento del LLM."
            }

if __name__ == "__main__":
    # --- PRUEBA UNITARIA ---
    print("🧪 Iniciando prueba del Cerebro (Gemma-3)...")
    
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
        print("PISTA: Verifica tu GOOGLE_API_KEY en el .env")