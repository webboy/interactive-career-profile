from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.version import API_VERSION, API_VERSION_KEY
from app.db.models.system_metadata import SystemMetadata


async def get_api_version(session: AsyncSession) -> str:
    result = await session.execute(
        select(SystemMetadata.value).where(SystemMetadata.key == API_VERSION_KEY)
    )
    stored_version = result.scalar_one_or_none()
    return stored_version or API_VERSION


async def sync_api_version(session: AsyncSession) -> str:
    result = await session.execute(
        select(SystemMetadata).where(SystemMetadata.key == API_VERSION_KEY)
    )
    metadata = result.scalar_one_or_none()

    if metadata is None:
        session.add(SystemMetadata(key=API_VERSION_KEY, value=API_VERSION))
    elif metadata.value != API_VERSION:
        metadata.value = API_VERSION

    await session.commit()
    return API_VERSION
