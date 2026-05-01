from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app import __version__, health_router, settings, v1_router
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    startup_logger = get_logger("app.startup")
    startup_logger.info(
        "app.starting",
        env=settings.APP_ENV,
        version=__version__,
        host=settings.HOST,
        port=settings.PORT,
    )
    yield
    startup_logger.info("app.shutdown")


app = FastAPI(
    title="aigo-ai",
    version=__version__,
    description="아이고 청년 AI Internal API",
    lifespan=lifespan,
)


def _error_payload(code: str, message: str) -> dict:
    return {"detail": {"code": code, "message": message}}


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        body = {"detail": detail}
    else:
        body = _error_payload(
            "HTTP_ERROR",
            str(detail) if detail else "요청을 처리할 수 없습니다.",
        )
    return JSONResponse(status_code=exc.status_code, content=body, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": {
                "code": "INVALID_REQUEST",
                "message": "요청 형식이 올바르지 않습니다.",
                "errors": jsonable_encoder(exc.errors()),
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.error("app.unhandled_exception", error=str(exc), exc_type=type(exc).__name__)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_payload(
            "INTERNAL_ERROR",
            "서버 내부 오류가 발생했습니다.",
        ),
    )


app.include_router(health_router)
app.include_router(v1_router)
