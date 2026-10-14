import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.bootstrap import bootstrap
from app.core.config import settings
from app.core.exceptions import AppError
from app.tenancy.middleware import TenantMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sportyclub")


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await bootstrap()
    except Exception:  # noqa: BLE001
        logger.exception("No se pudo ejecutar el bootstrap (revisa migraciones y BD)")
    yield


app = FastAPI(
    title="SportyClub API",
    version="0.1.0",
    description="API REST multitenant para administracion de clubes deportivos",
    lifespan=lifespan,
)

app.add_middleware(TenantMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


app.include_router(api_router)
