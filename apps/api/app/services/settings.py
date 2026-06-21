from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.setting import Setting

SECRET_REDACTED_VALUE = "***REDACTED***"


def redact_setting_value(setting: Setting) -> str:
    if setting.is_secret:
        return SECRET_REDACTED_VALUE
    return setting.value


async def list_settings(session: AsyncSession) -> list[Setting]:
    result = await session.execute(select(Setting).order_by(Setting.key))
    return list(result.scalars().all())


async def get_setting(session: AsyncSession, key: str) -> Setting | None:
    result = await session.execute(select(Setting).where(Setting.key == key))
    return result.scalar_one_or_none()


async def upsert_setting(
    session: AsyncSession,
    key: str,
    value: str,
    is_secret: bool = False,
) -> Setting:
    setting = await get_setting(session, key)
    if setting is None:
        setting = Setting(key=key, value=value, is_secret=is_secret)
        session.add(setting)
    else:
        setting.value = value
        setting.is_secret = is_secret

    await session.commit()
    await session.refresh(setting)
    return setting
