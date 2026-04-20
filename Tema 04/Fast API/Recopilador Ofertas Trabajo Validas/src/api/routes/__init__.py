from src.api.routes.auth import router as auth_router
from src.api.routes.cv import router as cv_router
from src.api.routes.offers import router as offers_router
from src.api.routes.adaptations import router as adaptations_router

__all__ = ["auth_router", "cv_router", "offers_router", "adaptations_router"]
