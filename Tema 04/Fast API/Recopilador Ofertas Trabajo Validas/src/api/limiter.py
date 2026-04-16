"""Rate limiter utility for FastAPI routes.

This module provides access to the slowapi Limiter instance initialized by main.py.
Routes are imported AFTER set_limiter() is called to avoid circular imports.
"""

_limiter_instance = None


class MockLimiter:
    """Mock limiter for testing. Allows decorators to work without actual rate limiting."""

    def limit(self, rule):
        """Return a no-op decorator that accepts any function."""
        def decorator(func):
            return func
        return decorator


def set_limiter(limiter):
    """Set the global limiter instance. Called by main.py during initialization."""
    global _limiter_instance
    _limiter_instance = limiter


def get_limiter():
    """
    Get the global limiter instance. Used by route decorators.
    Returns a MockLimiter in tests, real limiter in production.
    """
    if _limiter_instance is None:
        return MockLimiter()
    return _limiter_instance
