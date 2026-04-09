#!/usr/bin/env python3
"""
Tests Simples para Plan 01 - Sin pytest
Ejecutar: python tests/test_plan_01_simple.py
"""
import asyncio
import os
import sys
from pathlib import Path

# Setup path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from dotenv import load_dotenv
load_dotenv()

# En Windows, forzar SelectorEventLoop para psycopg
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class TestResults:
    """Tracker simple para resultados de tests"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []

    def pass_test(self, name):
        self.passed += 1
        print(f"✅ {name}")

    def fail_test(self, name, error):
        self.failed += 1
        self.errors.append((name, str(error)))
        print(f"❌ {name}")
        print(f"   Error: {error}\n")

    def skip_test(self, name, reason):
        self.skipped += 1
        print(f"⏭️  {name} (Razón: {reason})")

    def print_summary(self):
        total = self.passed + self.failed + self.skipped
        print("\n" + "="*70)
        print("📊 RESUMEN DE TESTS")
        print("="*70)
        print(f"✅ Pasados:  {self.passed}")
        print(f"❌ Fallidos: {self.failed}")
        print(f"⏭️  Saltados: {self.skipped}")
        print(f"📈 Total:    {total}")

        if self.failed == 0:
            print("\n🎉 ¡TODOS LOS TESTS PASARON!")
        else:
            print(f"\n⚠️  {self.failed} test(s) fallaron:")
            for name, error in self.errors:
                print(f"   - {name}: {error}")

        print("="*70 + "\n")
        return self.failed == 0


results = TestResults()


def test_imports():
    """Test 1: Verificar que todos los módulos se importan correctamente"""
    try:
        from src.database import User, JobOffer, AsyncSessionLocal, get_db
        from src.mail_agent import GmailJobCollector, save_offer_to_db
        from src.bot import TelegramNotifier
        from src.cv_generator import CVGenerator
        from src.brain import RecruitmentBrain
        results.pass_test("test_imports: Todos los módulos importados")
    except Exception as e:
        results.fail_test("test_imports", e)


def test_telegram_keyboard():
    """Test 2: Verificar estructura del teclado Telegram"""
    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📄 Generar CV Optimizado", callback_data="gen_cv:123")]
        ])

        kb_dict = keyboard.to_dict()
        assert "inline_keyboard" in kb_dict
        assert len(kb_dict["inline_keyboard"]) == 1
        assert len(kb_dict["inline_keyboard"][0]) == 1

        button = kb_dict["inline_keyboard"][0][0]
        assert button["text"] == "📄 Generar CV Optimizado"
        assert button["callback_data"] == "gen_cv:123"

        results.pass_test("test_telegram_keyboard: Estructura válida")
    except AssertionError as e:
        results.fail_test("test_telegram_keyboard", f"Validación: {e}")
    except Exception as e:
        results.fail_test("test_telegram_keyboard", e)


def test_database_config():
    """Test 3: Verificar configuración de base de datos"""
    try:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            results.skip_test("test_database_config", "DATABASE_URL no configurada")
            return

        assert "postgresql" in db_url, "DATABASE_URL debe contener 'postgresql'"
        results.pass_test("test_database_config: DATABASE_URL válida")
    except Exception as e:
        results.fail_test("test_database_config", e)


def test_user_config():
    """Test 4: Verificar configuración de usuario"""
    try:
        user_id = os.getenv("USER_ID")
        user_email = os.getenv("USER_EMAIL")

        assert user_id, "USER_ID no configurado"
        assert user_email, "USER_EMAIL no configurado"

        # Validar formato UUID
        import uuid
        try:
            uuid.UUID(user_id)
        except ValueError:
            raise ValueError(f"USER_ID no es un UUID válido: {user_id}")

        results.pass_test("test_user_config: Configuración correcta")
    except Exception as e:
        results.fail_test("test_user_config", e)


def test_fastapi_endpoints():
    """Test 5: Verificar que los endpoints FastAPI están definidos"""
    try:
        from main import app

        routes = [route.path for route in app.routes if hasattr(route, 'path')]

        endpoints_required = ["/", "/health", "/api/generate/{offer_id}"]
        for endpoint in endpoints_required:
            assert endpoint in routes, f"Endpoint {endpoint} no encontrado"

        results.pass_test("test_fastapi_endpoints: Todos los endpoints presentes")
    except Exception as e:
        results.fail_test("test_fastapi_endpoints", e)


def test_callback_handler():
    """Test 6: Verificar callback handler de Telegram"""
    try:
        from src.bot import TelegramNotifier
        import inspect

        assert hasattr(TelegramNotifier, 'handle_generate_cv_callback'), "Método no encontrado"

        method = getattr(TelegramNotifier, 'handle_generate_cv_callback')
        assert inspect.iscoroutinefunction(method), "No es async"

        results.pass_test("test_callback_handler: Handler implementado")
    except Exception as e:
        results.fail_test("test_callback_handler", e)


def test_cv_generator_methods():
    """Test 7: Verificar métodos de CVGenerator"""
    try:
        from src.cv_generator import CVGenerator

        métodos = ['generate_for_offer', '_compile_latex', '_build_latex_template']
        for método in métodos:
            assert hasattr(CVGenerator, método), f"Método {método} no encontrado"

        results.pass_test("test_cv_generator_methods: Todos los métodos presentes")
    except Exception as e:
        results.fail_test("test_cv_generator_methods", e)


def test_save_offer_function():
    """Test 8: Verificar función save_offer_to_db"""
    try:
        from src.mail_agent import save_offer_to_db
        import inspect

        assert inspect.iscoroutinefunction(save_offer_to_db), "No es async"

        sig = inspect.signature(save_offer_to_db)
        params = list(sig.parameters.keys())
        expected = ['analysis', 'offer_url', 'raw_text', 'user_id']
        assert params == expected, f"Parámetros incorrectos: {params}"

        results.pass_test("test_save_offer_function: Función correcta")
    except Exception as e:
        results.fail_test("test_save_offer_function", e)


def test_requirements():
    """Test 9: Verificar dependencias en requirements.txt"""
    try:
        with open('requirements.txt', 'r') as f:
            reqs = f.read()

        libs = [
            'fastapi',
            'sqlalchemy[asyncio]',
            'asyncpg',
            'langchain-openai',
            'python-telegram-bot',
            'httpx',
            'cloudinary'
        ]

        for lib in libs:
            assert lib in reqs, f"Librería {lib} no encontrada"

        results.pass_test("test_requirements: Dependencias correctas")
    except Exception as e:
        results.fail_test("test_requirements", e)


async def test_offer_persistence():
    """Test 10: Persistencia de ofertas en BD (async)"""
    try:
        from src.database import AsyncSessionLocal, JobOffer, User
        from src.mail_agent import save_offer_to_db
        from sqlalchemy import select, delete

        user_id = os.getenv("USER_ID")
        if not user_id:
            results.skip_test("test_offer_persistence", "USER_ID no configurado")
            return

        # 1. Verificar/crear usuario
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                user = User(
                    id=user_id,
                    email=os.getenv("USER_EMAIL", "test@example.com"),
                    telegram_id=os.getenv("TELEGRAM_CHAT_ID")
                )
                session.add(user)
                await session.commit()

        # 2. Crear oferta
        analysis = {
            "match": True,
            "match_score": 85,
            "job_title": "Test Developer",
            "company": "Test Corp",
            "salary": "50k",
            "benefits": "Remote",
            "summary": "Test offer",
            "posted_date": "Today"
        }

        offer_id = await save_offer_to_db(
            analysis=analysis,
            offer_url="https://test.com/job",
            raw_text="Test content",
            user_id=user_id
        )

        # 3. Verificar que se guardó
        async with AsyncSessionLocal() as session:
            stmt = select(JobOffer).where(JobOffer.id == offer_id)
            result = await session.execute(stmt)
            offer = result.scalar_one_or_none()

        assert offer is not None, "Oferta no se guardó"
        assert offer.job_title == "Test Developer"
        assert offer.score == 85

        # 4. Limpiar
        async with AsyncSessionLocal() as session:
            stmt = delete(JobOffer).where(JobOffer.id == offer_id)
            await session.execute(stmt)
            await session.commit()

        results.pass_test("test_offer_persistence: Persistencia correcta")
    except Exception as e:
        results.fail_test("test_offer_persistence", e)


async def run_async_tests():
    """Ejecutar todos los tests async"""
    await test_offer_persistence()


def main():
    """Ejecutar todos los tests"""
    print("\n" + "="*70)
    print("🧪 PLAN 01 - TESTS SIMPLES (sin pytest)")
    print("="*70 + "\n")

    # Tests síncronos
    test_imports()
    test_telegram_keyboard()
    test_database_config()
    test_user_config()
    test_fastapi_endpoints()
    test_callback_handler()
    test_cv_generator_methods()
    test_save_offer_function()
    test_requirements()

    # Tests async
    asyncio.run(run_async_tests())

    # Resumen
    success = results.print_summary()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
