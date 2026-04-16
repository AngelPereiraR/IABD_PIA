def __getattr__(name):
    """Lazy import routers to avoid circular imports with limiter setup."""
    if name == "cv_router":
        from src.api.routes import cv_router
        return cv_router
    elif name == "offers_router":
        from src.api.routes import offers_router
        return offers_router
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["cv_router", "offers_router"]
