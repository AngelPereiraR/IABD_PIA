import google.generativeai as genai
import os
import numpy as np
import tkinter as tk
from tkinter import filedialog
import pickle
from pypdf import PdfReader  # <-- NUEVA IMPORTACIÓN
from dotenv import load_dotenv

# --- Configuración y Modelos ---
MODELO_EMBEDDING = "models/text-embedding-004"
MODELO_GENERATIVO = "models/gemini-2.5-pro" 

# --- Funciones de API y Similitud (Sin cambios) ---

def configurar_api():
    """Configura la API de Gemini usando la variable de entorno."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Error: 'GEMINI_API_KEY' no está configurada.")
    genai.configure(api_key=api_key) # type: ignore
    print("✅ API de Gemini configurada.")

def obtener_embedding(texto: str, task_type: str) -> np.ndarray:
    """Obtiene el vector de embedding para un texto dado."""
    try:
        if len(texto.encode('utf-8')) > 35000:
             print(f"Advertencia: Chunk demasiado grande ({len(texto.encode('utf-8'))} bytes), saltando.")
             return np.array([])
        result = genai.embed_content( # type: ignore
            model=MODELO_EMBEDDING,
            content=texto,
            task_type=task_type
        )
        return np.array(result['embedding'])
    except Exception as e:
        print(f"Error al generar embedding: {e}")
        return np.array([])

def calcular_similitud_coseno(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calcula la similitud de coseno entre dos vectores numpy."""
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    if norm_vec1 == 0 or norm_vec2 == 0:
        return 0.0
    return dot_product / (norm_vec1 * norm_vec2)

# --- Funciones de Archivo (Selector y Lector) ---

def seleccionar_archivo() -> str:
    """Abre un diálogo gráfico de Tkinter para seleccionar un archivo."""
    root = tk.Tk()
    root.withdraw()
    print("Abriendo diálogo de selección de archivo...")
    ruta_archivo = filedialog.askopenfilename(
        title="Selecciona tu documento (.txt o .pdf)",
        filetypes=(
            ("Documentos Soportados", "*.txt *.pdf"),
            ("Archivos de texto", "*.txt"),
            ("Archivos PDF", "*.pdf"),
            ("Todos los archivos", "*.*")
        )
    )
    root.destroy()
    return ruta_archivo

# --- FUNCIÓN DE LECTURA ACTUALIZADA ---

def leer_documento_externo(ruta_archivo: str) -> str:
    """
    Lee el contenido de un archivo, extrayendo texto de .pdf o .txt.
    """
    print(f"Leyendo documento desde: {ruta_archivo}")
    
    # Obtenemos la extensión del archivo
    _, extension = os.path.splitext(ruta_archivo)
    
    # --- Lógica para PDF ---
    if extension.lower() == '.pdf':
        try:
            print("Detectado archivo PDF. Usando PyPDF para extraer texto...")
            texto_completo = ""
            # Los PDF se abren en modo 'read binary' (rb)
            with open(ruta_archivo, 'rb') as f:
                reader = PdfReader(f)
                num_paginas = len(reader.pages)
                print(f"Total de páginas: {num_paginas}")
                
                for i, page in enumerate(reader.pages):
                    texto = page.extract_text()
                    if texto:
                        texto_completo += texto
                    # Opcional: mostrar progreso
                    # print(f"Leyendo página {i+1}/{num_paginas}...")
            
            if not texto_completo:
                print("Advertencia: El PDF no contenía texto extraíble (podría ser una imagen).")
                return ""
            
            print("✅ Texto de PDF extraído exitosamente.")
            return texto_completo
            
        except Exception as e:
            print(f"Error al leer el PDF con PyPDF: {e}")
            return ""
    
    # --- Lógica para TXT (la que ya tenías) ---
    elif extension.lower() == '.txt':
        print("Detectado archivo TXT. Usando lector de texto plano...")
        encodings_a_probar = ['utf-8', 'utf-16', 'latin-1', 'windows-1252']
        for encoding in encodings_a_probar:
            try:
                with open(ruta_archivo, 'r', encoding=encoding) as f:
                    contenido = f.read()
                if not contenido:
                    raise ValueError("El archivo está vacío.")
                print(f"✅ Documento leído exitosamente con encoding '{encoding}'.")
                return contenido
            except UnicodeDecodeError:
                print(f"  ... falló con encoding '{encoding}', probando el siguiente...")
                continue
            except Exception as e:
                print(f"Error inesperado al leer el archivo TXT: {e}")
                return ""
        print(f"Error: No se pudo decodificar el archivo TXT. Se probaron: {encodings_a_probar}")
        return ""
        
    # --- Otros tipos de archivo ---
    else:
        print(f"Error: Tipo de archivo '{extension}' no soportado. Solo .txt y .pdf")
        return ""


# --- Funciones RAG (Sin cambios) ---

def chunk_texto_flexible(texto: str, chunk_size: int = 4000, overlap: int = 400) -> list[str]:
    """Divide el texto en chunks de tamaño fijo con superposición."""
    if len(texto) == 0:
        return []
    chunks = []
    start = 0
    while start < len(texto):
        end = start + chunk_size
        chunks.append(texto[start:end])
        start += chunk_size - overlap
    return chunks

def indexar_documento(documento: str) -> list[dict]:
    """Proceso LENTO: Divide el documento y genera embeddings."""
    print(f"\nIndexando documento... (usando {MODELO_EMBEDDING})")
    chunks = chunk_texto_flexible(documento)
    if not chunks:
        print("Error: El documento está vacío o no se pudo dividir en chunks.")
        return []
    db_vectorial = []
    for i, chunk in enumerate(chunks):
        print(f"Procesando chunk {i+1}/{len(chunks)}...")
        emb = obtener_embedding(chunk, "RETRIEVAL_DOCUMENT")
        if emb.size > 0:
            db_vectorial.append({"texto": chunk, "embedding": emb})
    print(f"✅ Documento indexado en {len(db_vectorial)} chunks.")
    return db_vectorial

# --- Funciones de Persistencia (Sin cambios) ---

def guardar_indice_vectorial(db: list[dict], ruta_indice: str):
    """
    Guarda la base de datos vectorial en un archivo pickle.
    Crea el directorio de destino si no existe.
    """
    try:
        directorio = os.path.dirname(ruta_indice)
        if directorio and not os.path.exists(directorio):
            print(f"Creando directorio de caché: {directorio}")
            os.makedirs(directorio)
        print(f"\nGuardando índice en: {ruta_indice}")
        with open(ruta_indice, 'wb') as f:
            pickle.dump(db, f)
        print("✅ Índice guardado para uso futuro.")
    except Exception as e:
        print(f"Error al guardar el índice: {e}")

def cargar_indice_vectorial(ruta_indice: str) -> list[dict] | None:
    """Carga la base de datos vectorial desde un archivo pickle."""
    print(f"Intentando cargar índice existente desde: {ruta_indice}")
    try:
        with open(ruta_indice, 'rb') as f:
            db = pickle.load(f)
        print("✅ Índice cargado exitosamente.")
        return db
    except FileNotFoundError:
        print("... No se encontró un índice guardado.")
        return None
    except Exception as e:
        print(f"Error al cargar el índice (archivo corrupto?): {e}")
        return None

# --- Funciones de Búsqueda y Generación (Sin cambios) ---

def encontrar_contexto_relevante(pregunta_emb: np.ndarray, db_vectorial: list[dict]) -> str:
    """Encuentra el chunk de texto más relevante (mayor similitud)."""
    mejor_similitud = -1.0
    mejor_contexto = "No se encontró contexto relevante."
    for item in db_vectorial:
        similitud = calcular_similitud_coseno(pregunta_emb, item['embedding'])
        if similitud > mejor_similitud:
            mejor_similitud = similitud
            mejor_contexto = item['texto']
    print(f"\nℹ️ Contexto encontrado con similitud: {mejor_similitud:.4f}")
    return mejor_contexto

def generar_respuesta_rag(pregunta: str, contexto: str) -> str:
    """Genera una respuesta a la pregunta usando el modelo generativo."""
    print(f"Generando respuesta... (usando {MODELO_GENERATIVO})")
    
    modelo_gen = genai.GenerativeModel(MODELO_GENERATIVO) # type: ignore
    
    prompt = f"""
    Eres un asistente experto. Responde la pregunta basándote ÚNICA Y EXCLUSIVAMENTE 
    en el contexto proporcionado.
    Si la respuesta no se encuentra en el contexto, di "La información no se encuentra en el documento."

    Contexto:
    {contexto}
    ---
    Pregunta:
    {pregunta}
    ---
    Respuesta:
    """
    try:
        response = modelo_gen.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error al generar respuesta: {e}"

# --- Función Principal (Sin cambios) ---

def main():
    try:
        configurar_api()
        
        # --- FASE 0: OBTENER EL DOCUMENTO ---
        print("\n--- Carga del Documento ---")
        ruta_archivo = seleccionar_archivo()
        if not ruta_archivo:
            print("❌ No se seleccionó ningún archivo. Abortando.")
            return
        print(f"✅ Archivo seleccionado: {ruta_archivo}")

        # --- FASE 1: INDEXACIÓN (Ahora con caché) ---
        
        DB_FOLDER = "/home/manuel/Documentos/IA_BigData/PIA/PIA_UD2/embeddings"
        nombre_base = os.path.basename(ruta_archivo)
        nombre_indice = f"{nombre_base}.pkl"
        ruta_indice = os.path.join(DB_FOLDER, nombre_indice) 
        
        db_vectorial = None

        if os.path.exists(ruta_indice):
            db_vectorial = cargar_indice_vectorial(ruta_indice)
        
        if db_vectorial is None:
            print("No se encontró índice. Creando uno nuevo...")
            # Aquí es donde se llama a la nueva función
            documento_texto = leer_documento_externo(ruta_archivo)
            if not documento_texto:
                print("No se pudo leer el documento. Abortando.")
                return

            db_vectorial = indexar_documento(documento_texto)
            
            if db_vectorial:
                guardar_indice_vectorial(db_vectorial, ruta_indice)
        
        if not db_vectorial:
            print("Error fatal: No se pudo cargar o crear la base de datos vectorial.")
            return

        print("-" * 30)
        
        # --- FASE 2: CONSULTA (Bucle) ---
        print("\n--- Inicio de Consulta RAG ---")
        print("Puedes hacer preguntas sobre el documento. Escribe 'salir' para terminar.")
        
        while True:
            pregunta_usuario = input("\nTu pregunta: ")
            if pregunta_usuario.lower() == 'salir':
                print("¡Hasta luego!")
                break
                
            pregunta_emb = obtener_embedding(pregunta_usuario, "RETRIEVAL_QUERY")
            if pregunta_emb.size == 0:
                print("No se pudo procesar la pregunta.")
                continue
            contexto_relevante = encontrar_contexto_relevante(pregunta_emb, db_vectorial)
            respuesta = generar_respuesta_rag(pregunta_usuario, contexto_relevante)
            print("\n=== Respuesta ===")
            print(respuesta)

    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"Ha ocurrido un error inesperado: {e}")

if __name__ == "__main__":
    main()