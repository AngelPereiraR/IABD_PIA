import json
import os
from datetime import datetime, timedelta
from langchain_google_community.gmail.utils import get_gmail_credentials

class TokenManager:
    """
    Gestiona tokens OAuth 2.0 de Gmail con renovación automática.
    Detecta expiración y regenera tokens cuando es necesario.
    """

    TOKEN_FILE = "token.json"
    CREDENTIALS_FILE = "credentials.json"
    EXPIRY_BUFFER = 300  # Considerar expirado 5 min antes de la hora real

    @staticmethod
    def is_token_valid() -> bool:
        """
        Verifica si el token.json existe y no ha expirado.

        Returns:
            bool: True si el token es válido y usable
        """
        if not os.path.exists(TokenManager.TOKEN_FILE):
            return False

        try:
            with open(TokenManager.TOKEN_FILE, 'r') as f:
                token_data = json.load(f)

            # Verificar que tenga los campos requeridos
            if 'expiry' not in token_data or 'refresh_token' not in token_data:
                return False

            # Convertir timestamp ISO a datetime (remove timezone para comparación)
            expiry_str = token_data['expiry']
            # Remover 'Z' si existe
            if expiry_str.endswith('Z'):
                expiry_str = expiry_str[:-1]
            expiry = datetime.fromisoformat(expiry_str)
            now = datetime.utcnow()

            # Si el token expira en menos de EXPIRY_BUFFER segundos, considerarlo expirado
            if now >= (expiry - timedelta(seconds=TokenManager.EXPIRY_BUFFER)):
                print(f"[TOKEN] Access token expirado el {expiry}. Necesita renovación.")
                return False

            print(f"[TOKEN] Access token válido hasta {expiry}")
            return True

        except Exception as e:
            print(f"[TOKEN] Error al verificar token: {e}")
            return False

    @staticmethod
    def generate_new_token() -> bool:
        """
        Genera un token NUEVO mediante flujo OAuth completo.
        Se usa la primera vez o cuando el refresh token ha expirado.

        Returns:
            bool: True si se generó exitosamente
        """
        try:
            print(f"[TOKEN] Iniciando flujo OAuth para generar nuevo token...")

            # LangChain maneja todo: abre navegador, recibe código, guarda token.json
            creds = get_gmail_credentials(
                scopes=["https://mail.google.com/"],
            )

            # Verificar que se guardó
            if os.path.exists(TokenManager.TOKEN_FILE):
                print(f"[TOKEN] ✅ Nuevo token generado exitosamente")
                return True
            else:
                print(f"[TOKEN] ❌ Token no se guardó correctamente")
                return False

        except Exception as e:
            print(f"[TOKEN] ❌ Error al generar token: {e}")
            return False

    @staticmethod
    def refresh_token() -> bool:
        """
        Intenta renovar el access token usando el refresh token existente.
        Si el archivo no existe, genera uno nuevo.

        Returns:
            bool: True si la renovación/generación fue exitosa
        """
        if not os.path.exists(TokenManager.TOKEN_FILE):
            print(f"[TOKEN] {TokenManager.TOKEN_FILE} no existe. Generando nuevo token...")
            return TokenManager.generate_new_token()

        try:
            print(f"[TOKEN] Intentando renovar token...")

            # LangChain intenta refrescar automáticamente si el token está expirado
            creds = get_gmail_credentials(
                scopes=["https://mail.google.com/"],
            )

            # Si llegamos aquí, la renovación fue exitosa
            print(f"[TOKEN] ✅ Token renovado exitosamente")
            return True

        except Exception as e:
            print(f"[TOKEN] ❌ Error al renovar token ({e}). Generando nuevo...")
            # Si la renovación falla, generar uno nuevo
            return TokenManager.generate_new_token()

    @staticmethod
    def ensure_valid_token() -> bool:
        """
        Garantiza que hay un token válido disponible.
        Intenta renovar si está expirado, requiere login si es necesario.

        Returns:
            bool: True si hay token válido, False si requiere login manual
        """
        # Si el token es válido, no hacer nada
        if TokenManager.is_token_valid():
            return True

        # Intentar renovar
        if TokenManager.refresh_token():
            return True

        # Si todo falla, requiere login manual
        print("\n" + "="*60)
        print("⚠️  REGENERACIÓN DE TOKEN REQUERIDA")
        print("="*60)
        print("\nEl token de Gmail ha expirado y no puede ser renovado automáticamente.")
        print("Ejecuta el siguiente comando para generar uno nuevo:\n")
        print("   python src/setup_auth.py\n")
        print("="*60 + "\n")
        return False

    @staticmethod
    def get_credentials():
        """
        Obtiene GmailToolkit con credenciales válidas.

        Returns:
            GmailToolkit configurado con token.json

        Raises:
            RuntimeError: Si el token ha expirado y no puede renovarse
        """
        if not TokenManager.ensure_valid_token():
            raise RuntimeError(
                "Token de Gmail expirado. "
                "Ejecuta 'python src/setup_auth.py' para generar uno nuevo."
            )

        try:
            from langchain_google_community import GmailToolkit
            return GmailToolkit()
        except Exception as e:
            raise RuntimeError(f"Error al obtener credenciales de Gmail: {e}")
