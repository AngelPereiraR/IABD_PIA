import google.generativeai as genai
import os

def configurar_api():
    """Configura la API de Gemini usando la variable de entorno."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: La variable de entorno 'GEMINI_API_KEY' no está configurada.")
        return False
    try:
        genai.configure(api_key=api_key) # type: ignore
        print("✅ API de Gemini configurada.")
        return True
    except Exception as e:
        print(f"Error al configurar la API: {e}")
        return False

def listar_modelos_disponibles():
    """
    Imprime los modelos generativos (los que pueden 'generar contenido')
    disponibles para tu clave API.
    """
    print("\n--- Buscando Modelos Generativos Disponibles ---")
    
    if not configurar_api():
        return

    try:
        modelos_encontrados = False
        # Esta función (list_models) requiere la biblioteca actualizada
        for m in genai.list_models(): # type: ignore
            # Nos interesan solo los modelos que pueden generar contenido (como gemini-pro)
            if 'generateContent' in m.supported_generation_methods:
                print(f"  ➡️  {m.name}")
                modelos_encontrados = True
        
        if not modelos_encontrados:
            print("No se encontraron modelos con 'generateContent' habilitado.")
            
        print("-------------------------------------------------")
        print("\nCopia el nombre EXACTO de uno de estos modelos (ej. 'models/gemini-1.0-pro')")
        print("y pégalo en la variable 'MODELO_GENERATIVO' de tu script RAG.")

    except Exception as e:
        print(f"\n--- ERROR ---")
        print(f"No se pudieron listar los modelos: {e}")
        print("Asegúrate de que tu clave API sea correcta y tengas conexión a internet.")

if __name__ == "__main__":
    listar_modelos_disponibles()