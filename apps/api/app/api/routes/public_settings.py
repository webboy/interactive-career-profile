from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.public import PublicSettingsResponse

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/settings", response_model=PublicSettingsResponse)
async def get_public_settings() -> PublicSettingsResponse:
    settings = get_settings()
    return PublicSettingsResponse(
        app_name=settings.app_name,
        app_url=settings.app_url,
        default_language=settings.default_language,
        supported_languages=settings.supported_language_list,
    )
