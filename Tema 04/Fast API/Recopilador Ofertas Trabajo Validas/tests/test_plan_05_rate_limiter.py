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

if __name__ == "__main__":
    unittest.main()
