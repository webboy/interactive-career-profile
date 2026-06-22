from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.admin_career_records import router as admin_career_records_router
from app.api.routes.admin_documents import chunk_router as admin_document_chunks_router
from app.api.routes.admin_documents import router as admin_documents_router
from app.api.routes.admin_legal import router as admin_legal_router
from app.api.routes.admin_profile import router as admin_profile_router
from app.api.routes.admin_settings import router as admin_settings_router
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.public_legal import router as public_legal_router
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
    app.include_router(auth_router)
    app.include_router(admin_settings_router)
    app.include_router(admin_profile_router)
    app.include_router(admin_career_records_router)
    app.include_router(admin_documents_router)
    app.include_router(admin_document_chunks_router)
    app.include_router(admin_legal_router)
    app.include_router(public_legal_router)
    return app


app = create_app()
