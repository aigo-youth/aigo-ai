from fastapi import APIRouter

from app.api.v1.chat import router as chat_router
from app.api.v1.embed import router as embed_router
from app.api.v1.pdf import router as pdf_router

v1_router = APIRouter(prefix="/v1", tags=["v1"])
v1_router.include_router(chat_router)
v1_router.include_router(pdf_router)
v1_router.include_router(embed_router)
