from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import require_admin_user
from app.db.models.user import User
from app.db.session import get_db_session
from app.schemas.settings import SettingResponse, SettingUpdateRequest
from app.services.settings import list_settings, redact_setting_value, upsert_setting

router = APIRouter(prefix="/api/admin/settings", tags=["admin-settings"])


@router.get("", response_model=list[SettingResponse])
async def get_settings(
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[SettingResponse]:
    settings = await list_settings(session)
    return [
        SettingResponse(
            key=setting.key,
            value=redact_setting_value(setting),
            is_secret=setting.is_secret,
        )
        for setting in settings
    ]


@router.put("/{key}", response_model=SettingResponse)
async def update_setting(
    key: str,
    payload: SettingUpdateRequest,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> SettingResponse:
    setting = await upsert_setting(
        session,
        key=key,
        value=payload.value,
        is_secret=payload.is_secret,
    )
    return SettingResponse(
        key=setting.key,
        value=redact_setting_value(setting),
        is_secret=setting.is_secret,
    )
