from app.api.health import router as health_router
from app.api.legacy import legacy_router
from app.api.v1.router import v1_router

__all__ = ["health_router", "legacy_router", "v1_router"]
