__version__ = "0.1.0"

from app.settings import settings
from app.api import health_router, legacy_router, v1_router

__all__ = [
  "__version__",
  "settings",
  "health_router",
  "legacy_router",
  "v1_router",
]
