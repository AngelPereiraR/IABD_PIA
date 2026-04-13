"""
Tests para Plan 04 - API FastAPI

Sin pytest - usando unittest
Cubre:
1. GET /api/offers/{offer_id}     → Detalle de una oferta
2. GET /api/offers/{offer_id}/cv  → Redirect a URL del PDF
3. Schemas: OfferDetail con optimized_cv_url
4. Estructura de rutas y métodos HTTP
5. CORS middleware configurado en main.py
"""

import unittest
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.schemas import OfferDetail
from src.api.routes.offers import router as offers_router


class TestPlan04Schemas(unittest.TestCase):
    """Tests para el modelo OfferDetail con optimized_cv_url"""

    def test_offer_detail_with_optimized_cv_url(self):
        """OfferDetail debe aceptar optimized_cv_url"""
        offer = OfferDetail(
            id=1,
            job_title="Python Developer",
            company="Acme",
            score=90,
            status="done",
            offer_url="https://linkedin.com/jobs/1",
            optimized_cv_url="https://res.cloudinary.com/cv.pdf",
            created_at=datetime.now(),
        )
        self.assertEqual(offer.optimized_cv_url, "https://res.cloudinary.com/cv.pdf")

    def test_offer_detail_optimized_cv_url_optional(self):
        """OfferDetail debe aceptar optimized_cv_url=None"""
        offer = OfferDetail(
            id=2,
            job_title="Backend Engineer",
            company="Beta Corp",
            score=75,
            status="pending",
            offer_url="https://infojobs.net/jobs/2",
            optimized_cv_url=None,
            created_at=datetime.now(),
        )
        self.assertIsNone(offer.optimized_cv_url)

    def test_offer_detail_all_optional_fields_none(self):
        """OfferDetail debe funcionar con solo campos requeridos"""
        offer = OfferDetail(
            id=3,
            status="new",
            created_at=datetime.now(),
        )
        self.assertEqual(offer.id, 3)
        self.assertIsNone(offer.job_title)
        self.assertIsNone(offer.company)
        self.assertIsNone(offer.score)
        self.assertIsNone(offer.offer_url)
        self.assertIsNone(offer.optimized_cv_url)


class TestPlan04OfferDetailRoute(unittest.TestCase):
    """Tests para GET /api/offers/{offer_id}"""

    def test_offers_router_has_detail_route(self):
        """offers_router debe tener ruta /api/offers/{offer_id}"""
        paths = [r.path for r in offers_router.routes if hasattr(r, "path")]
        self.assertIn("/api/offers/{offer_id}", paths)

    def test_offers_detail_route_is_get(self):
        """Ruta /api/offers/{offer_id} debe ser GET"""
        for route in offers_router.routes:
            if hasattr(route, "path") and route.path == "/api/offers/{offer_id}":
                if hasattr(route, "methods"):
                    self.assertIn("GET", route.methods)
                return
        self.fail("Ruta /api/offers/{offer_id} no encontrada")

    def test_offers_detail_route_response_model(self):
        """Ruta /api/offers/{offer_id} debe retornar OfferDetail"""
        for route in offers_router.routes:
            if hasattr(route, "path") and route.path == "/api/offers/{offer_id}":
                self.assertEqual(route.response_model, OfferDetail)
                return
        self.fail("Ruta /api/offers/{offer_id} no encontrada")


class TestPlan04OfferCVRoute(unittest.TestCase):
    """Tests para GET /api/offers/{offer_id}/cv"""

    def test_offers_router_has_cv_route(self):
        """offers_router debe tener ruta /api/offers/{offer_id}/cv"""
        paths = [r.path for r in offers_router.routes if hasattr(r, "path")]
        self.assertIn("/api/offers/{offer_id}/cv", paths)

    def test_offers_cv_route_is_get(self):
        """Ruta /api/offers/{offer_id}/cv debe ser GET"""
        for route in offers_router.routes:
            if hasattr(route, "path") and route.path == "/api/offers/{offer_id}/cv":
                if hasattr(route, "methods"):
                    self.assertIn("GET", route.methods)
                return
        self.fail("Ruta /api/offers/{offer_id}/cv no encontrada")


class TestPlan04FileContent(unittest.TestCase):
    """Tests de contenido del archivo offers.py"""

    def setUp(self):
        self.offers_file = Path(__file__).parent.parent / "src" / "api" / "routes" / "offers.py"
        self.content = self.offers_file.read_text(encoding="utf-8")

    def test_get_offer_function_exists(self):
        """offers.py debe tener función get_offer"""
        self.assertIn("async def get_offer(", self.content)

    def test_get_offer_cv_function_exists(self):
        """offers.py debe tener función get_offer_cv"""
        self.assertIn("async def get_offer_cv(", self.content)

    def test_redirect_response_imported(self):
        """offers.py debe importar RedirectResponse"""
        self.assertIn("RedirectResponse", self.content)

    def test_404_on_not_found(self):
        """offers.py debe lanzar 404 cuando la oferta no existe"""
        self.assertIn("status_code=404", self.content)

    def test_redirect_on_cv_url(self):
        """offers.py debe redirigir a optimized_cv_url"""
        self.assertIn("return RedirectResponse(url=offer.optimized_cv_url)", self.content)

    def test_cv_not_generated_404(self):
        """offers.py debe lanzar 404 si CV no fue generado"""
        self.assertIn("CV aún no generado", self.content)


class TestPlan04MainAppRoutes(unittest.TestCase):
    """Tests para verificar que main.py expone todos los endpoints del plan"""

    def setUp(self):
        import main
        self.app = main.app
        self.routes = [r.path for r in self.app.routes if hasattr(r, "path")]

    def test_offers_list_route_registered(self):
        """/api/offers debe estar registrado"""
        self.assertIn("/api/offers", self.routes)

    def test_offers_detail_route_registered(self):
        """/api/offers/{offer_id} debe estar registrado"""
        self.assertIn("/api/offers/{offer_id}", self.routes)

    def test_offers_cv_route_registered(self):
        """/api/offers/{offer_id}/cv debe estar registrado"""
        self.assertIn("/api/offers/{offer_id}/cv", self.routes)

    def test_generate_route_registered(self):
        """/api/generate/{offer_id} debe estar registrado"""
        has_generate = any("generate" in r for r in self.routes)
        self.assertTrue(has_generate, f"No encontré endpoint de generación en: {self.routes}")

    def test_upload_master_cv_route_registered(self):
        """/api/upload-master-cv debe estar registrado"""
        self.assertIn("/api/upload-master-cv", self.routes)


class TestPlan04CORSMiddleware(unittest.TestCase):
    """Tests para verificar CORS configurado en main.py"""

    def test_cors_middleware_present(self):
        """main.py debe tener CORSMiddleware configurado"""
        main_file = Path(__file__).parent.parent / "main.py"
        content = main_file.read_text(encoding="utf-8")
        self.assertIn("CORSMiddleware", content)

    def test_cors_allows_localhost(self):
        """CORS debe permitir localhost (dev)"""
        main_file = Path(__file__).parent.parent / "main.py"
        content = main_file.read_text(encoding="utf-8")
        self.assertIn("localhost", content)


def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestPlan04Schemas))
    suite.addTests(loader.loadTestsFromTestCase(TestPlan04OfferDetailRoute))
    suite.addTests(loader.loadTestsFromTestCase(TestPlan04OfferCVRoute))
    suite.addTests(loader.loadTestsFromTestCase(TestPlan04FileContent))
    suite.addTests(loader.loadTestsFromTestCase(TestPlan04MainAppRoutes))
    suite.addTests(loader.loadTestsFromTestCase(TestPlan04CORSMiddleware))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit(run_tests())
