import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from redis.exceptions import RedisError

from src.core.config import get_settings
from src.core.exceptions import AppError
from src.core.redis import close_redis_client, get_redis_client
from src.tasks.router import router as tasks_router
from src.users.router import router as users_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        await get_redis_client().ping()
    except RedisError as exc:
        logger.warning("Redis ping failed on startup: %s", exc)

    yield

    await close_redis_client()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.project_name, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(users_router, prefix=settings.api_v1_prefix)
    app.include_router(tasks_router, prefix=settings.api_v1_prefix)

    frontend_dir = Path(__file__).parent / "frontend"
    if frontend_dir.exists():
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

    return app


app = create_app()
