import os
from dotenv import load_dotenv
# Importamos solo lo necesario para la autenticacion
from langchain_google_community.gmail.utils import get_gmail_credentials

# Cargar variables de entorno por si acaso
load_dotenv()

def generate_token():
    """
    Ejecuta el flujo de autenticacion OAuth local.
    Abre el navegador, pide permisos y guarda el token.json.
    """
    print("\n" + "="*60)
    print("🔑 GENERADOR DE TOKENS DE GMAIL (OAuth 2.0)")
    print("="*60)
    
    # Verificamos que exista credentials.json
    if not os.path.exists("credentials.json"):
        print("\n❌ Error: No se encuentra 'credentials.json' en la raiz.")
        print("   Por favor, descarga tus credenciales de OAuth desde Google Cloud Console.")
        print("   y guardalas con ese nombre en la misma carpeta que este script.")
        return

    print("\n1. Se abrira una ventana de navegador.")
    print("2. Inicia sesion con tu cuenta de Google.")
    print("3. Si ves una advertencia de 'Aplicacion no verificada', dale a Avanzado -> Ir a ... (inseguro).")
    print("4. Concede los permisos de lectura/escritura de Gmail.")
    print("\nPresiona ENTER para comenzar...")
    input()

    try:
        # Esta funcion de LangChain maneja todo el flujo:
        # - Lee credentials.json
        # - Abre el puerto local
        # - Lanza el navegador
        # - Recibe el codigo
        # - Genera y guarda token.json automaticamente
        creds = get_gmail_credentials(
            token_file="token.json",
            client_sercret_file="credentials.json",
            scopes=["https://mail.google.com/"], # Scope completo necesario para leer/borrar
        )
        
        if os.path.exists("token.json"):
            print("\n✅ ¡EXITO! Archivo 'token.json' generado correctamente.")
            print("-" * 60)
            print("AHORA: Copia el contenido de este archivo y pegalo en la variable")
            print("de entorno GOOGLE_TOKEN_JSON en Render/Railway.")
            print("-" * 60)
        else:
            print("\n⚠️ Algo salio mal. El proceso termino pero no veo el archivo token.json.")

    except Exception as e:
        print(f"\n❌ Error durante la autenticacion: {e}")

if __name__ == "__main__":
    generate_token()