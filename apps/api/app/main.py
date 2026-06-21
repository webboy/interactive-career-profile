from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.core.version import API_VERSION
from app.db.session import close_engine, get_session_factory
from app.services.version import sync_api_version


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings

    session_factory = get_session_factory()
    async with session_factory() as session:
        await sync_api_version(session)

    yield

    await close_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=API_VERSION,
        lifespan=lifespan,
    )
    app.include_router(health_router)
    return app


app = create_app()
