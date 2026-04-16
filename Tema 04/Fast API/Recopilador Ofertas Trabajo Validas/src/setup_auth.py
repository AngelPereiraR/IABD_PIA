import os
from dotenv import load_dotenv
from token_manager import TokenManager

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
        # Usar TokenManager para generar el token
        if TokenManager.refresh_token():
            print("\n✅ ¡EXITO! Archivo 'token.json' generado correctamente.")
            print("-" * 60)
            print("El bot usará este token automáticamente.")
            print("-" * 60)
        else:
            print("\n⚠️ Algo salio mal durante la autenticacion.")

    except Exception as e:
        print(f"\n❌ Error durante la autenticacion: {e}")

if __name__ == "__main__":
    generate_token()
