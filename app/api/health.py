from fastapi import APIRouter
from pydantic import BaseModel

from app.settings import settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
  status: str
  version: str
  env: str


@router.get("/health", response_model=HealthResponse)
async def health():
  from app import __version__
  return HealthResponse(
    status="ok",
    version=__version__,
    env=settings.APP_ENV,
  )