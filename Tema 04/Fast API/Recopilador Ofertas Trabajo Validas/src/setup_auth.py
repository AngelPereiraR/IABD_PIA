import os
from dotenv import load_dotenv
from token_manager import TokenManager

# Cargar variables de entorno por si acaso
load_dotenv()

def generate_token():
    """
    Ejecuta el flujo de autenticacion OAuth 2.0 local.
    Abre el navegador, pide permisos y guarda el token.json.

    ⚠️ NOTA: Solo necesario si NO usas Service Account.
    Si tienes service-account.json, el bot usará eso automáticamente.
    """
    print("\n" + "="*60)
    print("🔑 GENERADOR DE TOKENS DE GMAIL (OAuth 2.0)")
    print("="*60)

    # Verificar si ya existe service-account.json
    if os.path.exists(TokenManager.SERVICE_ACCOUNT_FILE):
        print(f"\n✅ Se encontró '{TokenManager.SERVICE_ACCOUNT_FILE}'.")
        print("   El bot usará Service Account automáticamente.")
        print("   No necesitas ejecutar este script.\n")
        return

    # Verificamos que exista credentials.json
    if not os.path.exists(TokenManager.CREDENTIALS_FILE):
        print(f"\n❌ Error: No se encuentra '{TokenManager.CREDENTIALS_FILE}' en la raiz.")
        print("   Por favor, descarga tus credenciales de OAuth desde Google Cloud Console.")
        print("   y guardalas con ese nombre en la misma carpeta que este script.")
        print("\n   Alternativa: Usa Service Account (recomendado).")
        print("   Ver SERVICE_ACCOUNT_SETUP.md para más info.\n")
        return

    print("\n1. Se abrira una ventana de navegador.")
    print("2. Inicia sesion con tu cuenta de Google.")
    print("3. Si ves una advertencia de 'Aplicacion no verificada', dale a Avanzado -> Ir a ... (inseguro).")
    print("4. Concede los permisos de lectura/escritura de Gmail.")
    print("\nPresiona ENTER para comenzar...")
    input()

    try:
        # Usar TokenManager para generar el token con validación integrada
        if TokenManager.refresh_token():
            print("\n✅ ¡EXITO! Archivo 'token.json' generado correctamente.")
            print("-" * 60)
            print("El bot usará 'token.json' automáticamente.")
            print("(Si colocas service-account.json, el bot lo preferirá)")
            print("-" * 60)
        else:
            print("\n⚠️ Algo salio mal durante la autenticacion.")
            print("Considera usar Service Account en su lugar.")
            print("Ver SERVICE_ACCOUNT_SETUP.md para más info.\n")

    except Exception as e:
        print(f"\n❌ Error durante la autenticacion: {e}")

if __name__ == "__main__":
    generate_token()