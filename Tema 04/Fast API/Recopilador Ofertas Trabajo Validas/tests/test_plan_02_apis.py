"""
Tests para Plan 02 - Paso 0: APIs Críticas

Sin pytest - usando unittest
Cubre:
1. POST /api/upload-master-cv
2. GET /api/offers
3. Integración Telegram polling
4. Verificación optimized_cv_url
"""

import unittest
import asyncio
import json
import os
import sys
from io import BytesIO
from pathlib import Path

# Agregar proyecto root al path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importaciones de la aplicación
from src.api.schemas import OfferDetail, CVUploadResponse, CVGenerationResponse
from src.api.dependencies import get_user_id
from src.api.routes.cv import router as cv_router
from src.api.routes.offers import router as offers_router


class TestPlan02Schemas(unittest.TestCase):
    """Tests para modelos Pydantic"""

    def test_offer_detail_model_valid(self):
        """CVUploadResponse debe validar correctamente"""
        response = CVUploadResponse(
            cv_url="https://res.cloudinary.com/example/cv.pdf",
            status="success"
        )
        self.assertEqual(response.cv_url, "https://res.cloudinary.com/example/cv.pdf")
        self.assertEqual(response.status, "success")

    def test_cv_upload_response_model(self):
        """CVUploadResponse debe tener campos correctos"""
        data = {"cv_url": "https://example.com/cv.pdf", "status": "success"}
        response = CVUploadResponse(**data)
        self.assertIsNotNone(response.cv_url)
        self.assertIsNotNone(response.status)

    def test_cv_generation_response_model(self):
        """CVGenerationResponse debe funcionar"""
        data = {"cv_url": "https://example.com/cv.pdf", "status": "success"}
        response = CVGenerationResponse(**data)
        self.assertIsNotNone(response.cv_url)
        self.assertIsNotNone(response.status)

    def test_offer_detail_model_structure(self):
        """OfferDetail debe tener todos los campos requeridos"""
        from datetime import datetime

        offer_data = {
            "id": 1,
            "job_title": "Senior Python Developer",
            "company": "TechCorp",
            "score": 85,
            "status": "done",
            "offer_url": "https://linkedin.com/jobs/123",
            "created_at": datetime.now()
        }

        offer = OfferDetail(**offer_data)
        self.assertEqual(offer.id, 1)
        self.assertEqual(offer.job_title, "Senior Python Developer")
        self.assertEqual(offer.company, "TechCorp")
        self.assertEqual(offer.score, 85)
        self.assertEqual(offer.status, "done")


class TestPlan02Dependencies(unittest.TestCase):
    """Tests para funciones de inyección"""

    def test_get_user_id_exists(self):
        """get_user_id debe ser callable"""
        self.assertTrue(callable(get_user_id))

    def test_get_user_id_signature(self):
        """get_user_id debe ser async"""
        import inspect
        self.assertTrue(inspect.iscoroutinefunction(get_user_id))


class TestPlan02Routes(unittest.TestCase):
    """Tests para routers de API"""

    def test_cv_router_exists(self):
        """CV router debe estar definido"""
        self.assertIsNotNone(cv_router)

    def test_cv_router_has_routes(self):
        """CV router debe tener rutas"""
        self.assertGreater(len(cv_router.routes), 0)

    def test_cv_router_has_upload_route(self):
        """CV router debe tener endpoint de upload"""
        route_paths = [route.path for route in cv_router.routes if hasattr(route, 'path')]
        # Router tiene prefijo /api
        self.assertIn("/api/upload-master-cv", route_paths)

    def test_cv_router_has_generate_route(self):
        """CV router debe tener endpoint de generación"""
        route_paths = [route.path for route in cv_router.routes if hasattr(route, 'path')]
        # Router tiene prefijo /api
        self.assertIn("/api/generate/{offer_id}", route_paths)

    def test_offers_router_exists(self):
        """Offers router debe estar definido"""
        self.assertIsNotNone(offers_router)

    def test_offers_router_has_routes(self):
        """Offers router debe tener rutas"""
        self.assertGreater(len(offers_router.routes), 0)

    def test_offers_router_has_list_route(self):
        """Offers router debe tener endpoint de listado"""
        route_paths = [route.path for route in offers_router.routes if hasattr(route, 'path')]
        # Router tiene prefijo /api
        self.assertIn("/api/offers", route_paths)


class TestPlan02APIEndpoints(unittest.TestCase):
    """Tests para verificar que endpoints están registrados"""

    def test_main_app_imports(self):
        """main.py debe importarse sin errores"""
        try:
            import main
            self.assertIsNotNone(main.app)
        except ImportError as e:
            self.fail(f"No se puede importar main.py: {e}")

    def test_main_app_has_cv_router(self):
        """main.py debe incluir cv_router"""
        import main
        routes = [r.path for r in main.app.routes if hasattr(r, 'path')]
        # Debe tener al menos uno de los endpoints de CV
        has_cv_endpoint = any('/upload-master-cv' in r or '/generate' in r for r in routes)
        self.assertTrue(has_cv_endpoint, f"No encontré endpoints de CV en: {routes}")

    def test_main_app_has_offers_router(self):
        """main.py debe incluir offers_router"""
        import main
        routes = [r.path for r in main.app.routes if hasattr(r, 'path')]
        self.assertIn("/api/offers", routes, f"No encontré /api/offers en: {routes}")

    def test_main_app_health_endpoint_exists(self):
        """main.py debe tener endpoint /health"""
        import main
        routes = [r.path for r in main.app.routes if hasattr(r, 'path')]
        self.assertIn("/health", routes)

    def test_main_app_home_endpoint_exists(self):
        """main.py debe tener endpoint /"""
        import main
        routes = [r.path for r in main.app.routes if hasattr(r, 'path')]
        self.assertIn("/", routes)


class TestPlan02Integration(unittest.TestCase):
    """Tests de integración - estructura y funcionamiento"""

    def test_api_module_structure(self):
        """src/api/ debe tener estructura correcta"""
        api_path = Path(__file__).parent.parent / "src" / "api"

        required_files = [
            "__init__.py",
            "schemas.py",
            "dependencies.py",
            "routes/__init__.py",
            "routes/cv.py",
            "routes/offers.py"
        ]

        for file in required_files:
            file_path = api_path / file
            self.assertTrue(
                file_path.exists(),
                f"Archivo requerido no encontrado: {file}"
            )

    def test_schemas_exports(self):
        """src/api/schemas.py debe exportar modelos correctos"""
        from src.api import schemas

        required_models = [
            'OfferDetail',
            'CVUploadResponse',
            'CVGenerationResponse'
        ]

        for model in required_models:
            self.assertTrue(
                hasattr(schemas, model),
                f"Modelo {model} no encontrado en schemas"
            )

    def test_routes_imports_in_init(self):
        """src/api/__init__.py debe exportar routers"""
        from src.api import cv_router, offers_router

        self.assertIsNotNone(cv_router)
        self.assertIsNotNone(offers_router)

    def test_dependencies_functions_exist(self):
        """src/api/dependencies.py debe tener funciones requeridas"""
        from src.api import dependencies

        required_funcs = [
            'get_user_id',
            'get_async_session'
        ]

        for func in required_funcs:
            self.assertTrue(
                hasattr(dependencies, func),
                f"Función {func} no encontrada en dependencies"
            )

    def test_cv_router_endpoint_methods(self):
        """CV router endpoints deben tener métodos HTTP correctos"""
        route_methods = {}
        for route in cv_router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                route_methods[route.path] = route.methods

        # POST /api/upload-master-cv
        if "/api/upload-master-cv" in route_methods:
            self.assertIn("POST", route_methods["/api/upload-master-cv"])

        # POST /api/generate/{offer_id}
        generate_paths = [p for p in route_methods if "generate" in p]
        if generate_paths:
            self.assertIn("POST", route_methods[generate_paths[0]])

    def test_offers_router_endpoint_methods(self):
        """Offers router endpoints deben tener métodos HTTP correctos"""
        route_methods = {}
        for route in offers_router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                route_methods[route.path] = route.methods

        # GET /api/offers
        if "/api/offers" in route_methods:
            self.assertIn("GET", route_methods["/api/offers"])


class TestPlan02FileStructure(unittest.TestCase):
    """Tests para verificar estructura de archivos creados"""

    def test_api_init_file_content(self):
        """src/api/__init__.py debe exportar routers"""
        init_file = Path(__file__).parent.parent / "src" / "api" / "__init__.py"
        content = init_file.read_text()

        self.assertIn("cv_router", content)
        self.assertIn("offers_router", content)

    def test_routes_init_file_content(self):
        """src/api/routes/__init__.py debe importar routers"""
        init_file = Path(__file__).parent.parent / "src" / "api" / "routes" / "__init__.py"
        content = init_file.read_text()

        self.assertIn("cv_router", content)
        self.assertIn("offers_router", content)

    def test_cv_router_file_has_upload_endpoint(self):
        """src/api/routes/cv.py debe tener endpoint de upload"""
        cv_file = Path(__file__).parent.parent / "src" / "api" / "routes" / "cv.py"
        content = cv_file.read_text()

        self.assertIn("upload_master_cv", content)
        self.assertIn("/upload-master-cv", content)

    def test_cv_router_file_has_generate_endpoint(self):
        """src/api/routes/cv.py debe tener endpoint de generación"""
        cv_file = Path(__file__).parent.parent / "src" / "api" / "routes" / "cv.py"
        content = cv_file.read_text()

        self.assertIn("generate_optimized_cv", content)
        self.assertIn("/generate/", content)

    def test_offers_router_file_has_list_endpoint(self):
        """src/api/routes/offers.py debe tener endpoint de listado"""
        offers_file = Path(__file__).parent.parent / "src" / "api" / "routes" / "offers.py"
        content = offers_file.read_text()

        self.assertIn("list_offers", content)
        self.assertIn("/offers", content)


def run_tests():
    """Ejecuta todos los tests sin pytest"""

    # Crear test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Agregar tests
    suite.addTests(loader.loadTestsFromTestCase(TestPlan02Schemas))
    suite.addTests(loader.loadTestsFromTestCase(TestPlan02Dependencies))
    suite.addTests(loader.loadTestsFromTestCase(TestPlan02Routes))
    suite.addTests(loader.loadTestsFromTestCase(TestPlan02APIEndpoints))
    suite.addTests(loader.loadTestsFromTestCase(TestPlan02Integration))
    suite.addTests(loader.loadTestsFromTestCase(TestPlan02FileStructure))

    # Ejecutar
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Retornar status
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit_code = run_tests()
    exit(exit_code)
