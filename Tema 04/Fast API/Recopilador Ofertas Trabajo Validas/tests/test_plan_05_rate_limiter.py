import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app

class TestRateLimiterConfig(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_limiter_registered_on_app(self):
        """Limiter state must be attached to app."""
        self.assertTrue(hasattr(app.state, "limiter"))

    def test_429_handler_registered(self):
        """App must have a 429 exception handler."""
        from slowapi.errors import RateLimitExceeded
        self.assertIn(RateLimitExceeded, app.exception_handlers)

class TestOffersRateLimit(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_get_offers_accepts_normal_traffic(self):
        """Single request to /api/offers should return 200 or 400 (not 429)."""
        r = self.client.get("/api/offers")
        self.assertNotEqual(r.status_code, 429)

    def test_get_offer_detail_accepts_normal_traffic(self):
        """Single request to /api/offers/1 should return 200, 404, or 400 (not 429)."""
        r = self.client.get("/api/offers/1")
        self.assertNotEqual(r.status_code, 429)


class TestCVRateLimit(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_generate_endpoint_accepts_normal_traffic(self):
        """Single request to /api/generate/1 should return 200, 404, or 422 (not 429)."""
        r = self.client.post("/api/generate/1")
        self.assertNotEqual(r.status_code, 429)

    def test_upload_endpoint_accepts_normal_traffic(self):
        """Single request to /api/upload-master-cv should return 200, 422, or 500 (not 429)."""
        r = self.client.post("/api/upload-master-cv")
        self.assertNotEqual(r.status_code, 429)


if __name__ == "__main__":
    unittest.main()
