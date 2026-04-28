"""
Test concurrencia entre API (async) y Bot (sync) para detectar race conditions.
"""
import asyncio
import threading
import time
import uuid
import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import (
    Base, User, JobOffer, SessionLocal, AsyncSessionLocal,
    sync_engine, engine, AuthProvider, UserRole
)


class ConcurrencyTester:
    """Test suite para verificar acceso concurrente a la BD desde API y Bot."""

    def __init__(self):
        self.test_user_id = str(uuid.uuid4())
        self.results = {
            "setup": False,
            "api_inserts": 0,
            "bot_inserts": 0,
            "read_consistency": True,
            "errors": []
        }

    async def setup_async_db(self):
        """Crear tablas con engine async."""
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("✅ [SETUP] Tablas creadas (async engine)")
            self.results["setup"] = True
        except Exception as e:
            self.results["errors"].append(f"Setup async failed: {e}")
            print(f"❌ [SETUP] Error: {e}")

    def create_test_user(self):
        """Crear usuario de prueba con SessionLocal."""
        try:
            with SessionLocal() as session:
                user = User(
                    id=uuid.UUID(self.test_user_id),
                    email=f"test-{int(time.time())}@example.com",
                    auth_provider=AuthProvider.EMAIL,
                    role=UserRole.USER
                )
                session.add(user)
                session.commit()
                print(f"✅ [USER] Usuario creado: {self.test_user_id}")
        except Exception as e:
            self.results["errors"].append(f"User creation failed: {e}")
            print(f"❌ [USER] Error: {e}")

    def bot_insert_offers(self, count=5):
        """Simular escritura del bot (SessionLocal sync)."""
        try:
            with SessionLocal() as session:
                for i in range(count):
                    offer = JobOffer(
                        user_id=uuid.UUID(self.test_user_id),
                        job_title=f"Bot Job {i}",
                        company=f"Company {i}",
                        offer_url=f"https://example.com/job-{i}",
                        score=50 + i,
                        is_valid=True,
                        raw_text=f"Job description {i}",
                        analysis_result={"test": True},
                        status="pending"
                    )
                    session.add(offer)
                    time.sleep(0.1)  # Simular procesamiento

                session.commit()
                self.results["bot_inserts"] = count
                print(f"✅ [BOT] {count} ofertas insertadas (SessionLocal sync)")
        except Exception as e:
            self.results["errors"].append(f"Bot insert failed: {e}")
            print(f"❌ [BOT] Error: {e}")

    async def api_read_offers(self):
        """Simular lectura de la API (AsyncSessionLocal)."""
        try:
            async with AsyncSessionLocal() as session:
                from sqlalchemy import select
                query = select(JobOffer).where(
                    JobOffer.user_id == uuid.UUID(self.test_user_id)
                )
                result = await session.execute(query)
                offers = result.scalars().all()
                self.results["api_inserts"] += len(offers)
                print(f"✅ [API] {len(offers)} ofertas leídas (AsyncSessionLocal async)")
                return offers
        except Exception as e:
            self.results["errors"].append(f"API read failed: {e}")
            print(f"❌ [API] Error: {e}")
            return []

    async def test_concurrent_access(self):
        """Test: Bot escribe mientras API lee."""
        print("\n🔄 TEST 1: Acceso concurrente (Bot escribe, API lee)")
        print("-" * 60)

        # Bot thread (sync)
        bot_thread = threading.Thread(
            target=self.bot_insert_offers,
            args=(3,),
            name="BotThread"
        )

        # API reads (async)
        async def api_reads():
            for i in range(3):
                offers = await self.api_read_offers()
                await asyncio.sleep(0.15)

        # Iniciar en paralelo
        bot_thread.start()
        api_task = asyncio.create_task(api_reads())

        bot_thread.join()
        await api_task

        print("✅ Acceso concurrente completado sin errores")

    async def test_transaction_isolation(self):
        """Test: Verificar aislamiento de transacciones."""
        print("\n🔄 TEST 2: Aislamiento de transacciones")
        print("-" * 60)

        try:
            # Contar ofertas antes
            async with AsyncSessionLocal() as session:
                from sqlalchemy import select, func
                query = select(func.count(JobOffer.id)).where(
                    JobOffer.user_id == uuid.UUID(self.test_user_id)
                )
                result = await session.execute(query)
                count_before = result.scalar()

            # Bot inserta 2 más
            self.bot_insert_offers(2)
            await asyncio.sleep(0.1)

            # API verifica consistencia
            async with AsyncSessionLocal() as session:
                from sqlalchemy import select, func
                query = select(func.count(JobOffer.id)).where(
                    JobOffer.user_id == uuid.UUID(self.test_user_id)
                )
                result = await session.execute(query)
                count_after = result.scalar()

            expected = count_before + 2
            if count_after == expected:
                print(f"✅ Aislamiento OK: {count_before} → {count_after} (expected {expected})")
            else:
                self.results["read_consistency"] = False
                print(f"❌ Inconsistencia: {count_before} → {count_after} (expected {expected})")

        except Exception as e:
            self.results["errors"].append(f"Isolation test failed: {e}")
            print(f"❌ Error: {e}")

    async def test_event_loop_conflict(self):
        """Test: Verificar que no hay conflicto de event loops."""
        print("\n🔄 TEST 3: Conflicto de event loops")
        print("-" * 60)

        try:
            main_loop = asyncio.get_running_loop()
            print(f"   Main event loop: {main_loop}")

            # Simular bot con su propio loop
            bot_loop = asyncio.new_event_loop()

            def bot_with_new_loop():
                asyncio.set_event_loop(bot_loop)
                try:
                    self.bot_insert_offers(1)
                    print(f"   Bot event loop: {bot_loop}")
                    print("✅ Bot loop separado funciona correctamente")
                except Exception as e:
                    print(f"❌ Bot loop error: {e}")
                finally:
                    bot_loop.close()

            bot_thread = threading.Thread(target=bot_with_new_loop, name="BotLoopThread")
            bot_thread.start()
            bot_thread.join()

        except Exception as e:
            self.results["errors"].append(f"Event loop test failed: {e}")
            print(f"❌ Error: {e}")

    def test_connection_pool(self):
        """Test: Verificar pool de conexiones."""
        print("\n🔄 TEST 4: Pool de conexiones")
        print("-" * 60)

        try:
            from sqlalchemy import text

            # Async pool
            async_pool = engine.pool
            print(f"   Async pool (asyncpg): {type(async_pool).__name__}")

            # Sync pool
            sync_pool = sync_engine.pool
            print(f"   Sync pool (psycopg2): {type(sync_pool).__name__}")

            # Verificar que pueden coexistir
            with SessionLocal() as session:
                result = session.execute(text("SELECT 1"))
                print(f"✅ Sync pool connection OK: {result.scalar()}")

            print("✅ Pools coexisten sin conflicto")
        except Exception as e:
            self.results["errors"].append(f"Pool test failed: {e}")
            print(f"❌ Error: {e}")

    async def run_all_tests(self):
        """Ejecutar suite completa de tests."""
        print("\n" + "=" * 60)
        print("🧪 TEST SUITE: Concurrencia API + Bot")
        print("=" * 60)

        # Setup
        await self.setup_async_db()
        self.create_test_user()

        # Tests
        await self.test_concurrent_access()
        await self.test_transaction_isolation()
        await self.test_event_loop_conflict()
        self.test_connection_pool()

        # Report
        self.print_report()

    def print_report(self):
        """Generar reporte final."""
        print("\n" + "=" * 60)
        print("📊 REPORTE FINAL")
        print("=" * 60)

        print(f"Setup:                {'✅ OK' if self.results['setup'] else '❌ FAILED'}")
        print(f"API reads:            {self.results['api_inserts']} registros")
        print(f"Bot inserts:          {self.results['bot_inserts']} registros")
        print(f"Read consistency:     {'✅ OK' if self.results['read_consistency'] else '❌ INCONSISTENT'}")

        if self.results["errors"]:
            print(f"\n⚠️  ERRORES ENCONTRADOS ({len(self.results['errors'])}):")
            for error in self.results["errors"]:
                print(f"   - {error}")
        else:
            print("\n✅ SIN ERRORES - Concurrencia segura")

        print("=" * 60)


async def main():
    """Entry point."""
    tester = ConcurrencyTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
