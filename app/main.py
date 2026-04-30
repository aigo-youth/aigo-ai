from fastapi import FastAPI

from contextlib import asynccontextmanager

from app import __version__, settings, health_router, legacy_router, v1_router
from app.core.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(_app: FastAPI):
  configure_logging()
  logger = get_logger("app.startup")
  logger.info(
    "app.starting",
    env=settings.APP_ENV,
    version=__version__,
    host=settings.HOST,
    port=settings.PORT,
  )
  yield
  logger.info("app.shutdown")


app = FastAPI(
  title="aigo-ai",
  version=__version__,
  description="Aigo Youth FastAPI 기반 법률 RAG 챗봇 백엔드",
  lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(legacy_router)
app.include_router(v1_router)
