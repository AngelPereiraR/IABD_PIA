import os
from langchain_community.document_loaders import PyPDFLoader

def load_cv_context(file_path: str) -> str:
    """
    Carga un archivo PDF (CV) y convierte su contenido a texto plano
    para ser usado como contexto en el LLM.
    
    Args:
        file_path (str): Ruta relativa o absoluta al archivo PDF.
        
    Returns:
        str: El contenido completo del texto del CV.
    """
    # Verificación de existencia
    if not os.path.exists(file_path):
        # Intentamos buscarlo en la raíz si no está en la ruta dada, como fallback
        if os.path.exists(os.path.basename(file_path)):
            file_path = os.path.basename(file_path)
            print(f"Archivo no encontrado en ruta original, usando versión en raíz: {file_path}")
        else:
            raise FileNotFoundError(f"El archivo de CV no se encuentra en: {file_path}")

    try:
        print(f"Procesando CV desde: {file_path}...")
        
        # Inicializar el loader de LangChain
        loader = PyPDFLoader(file_path)
        
        # Cargar y separar por páginas
        pages = loader.load()
        
        if not pages:
            print("El PDF parece estar vacío o no contiene texto seleccionable (quizás es una imagen escaneada).")
            return ""

        # Unir todas las páginas en un solo bloque de texto con separadores claros
        full_text = "\n\n".join([page.page_content for page in pages])
        
        print(f"CV cargado con éxito: {len(pages)} página(s) procesada(s).")
        return full_text

    except Exception as e:
        print(f"Error crítico al procesar el PDF: {e}")
        return ""

if __name__ == "__main__":
    # --- PRUEBA UNITARIA ---
    # Esto permite ejecutar 'python src/loader.py' para probar solo este módulo
    
    # Construimos la ruta asumiendo que el script se corre desde la raíz del proyecto
    # Ruta esperada: ./data/cv_usuario.pdf
    expected_path = os.path.join("data", "cv_usuario.pdf")
    
    print("Iniciando prueba de carga de CV...")
    
    try:
        contexto = load_cv_context(expected_path)
        
        if contexto:
            print("\n--- VISTA PREVIA DEL CONTEXTO (Primeros 500 caracteres) ---")
            print("-" * 60)
            print(contexto[:500] + "...")
            print("-" * 60)
            print("La prueba ha sido exitosa.")
        else:
            print("La prueba falló: No se extrajo texto.")
            
    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        print("PISTA: Asegúrate de crear la carpeta 'data' y poner ahí tu 'cv_usuario.pdf'.")