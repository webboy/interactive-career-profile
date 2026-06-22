from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import Visibility
from app.db.models.profile_item import ProfileItem
from app.schemas.profile import ProfileItemCreateRequest, ProfileItemUpdateRequest


async def list_profile_items(
    session: AsyncSession,
    visibility: Visibility | None = None,
) -> list[ProfileItem]:
    query = select(ProfileItem).order_by(ProfileItem.sort_order, ProfileItem.id)
    if visibility is not None:
        query = query.where(ProfileItem.visibility == visibility)

    result = await session.execute(query)
    return list(result.scalars().all())


async def list_public_profile_items(session: AsyncSession) -> list[ProfileItem]:
    return await list_profile_items(session, visibility=Visibility.PUBLIC)


async def get_profile_item(session: AsyncSession, item_id: int) -> ProfileItem | None:
    result = await session.execute(select(ProfileItem).where(ProfileItem.id == item_id))
    return result.scalar_one_or_none()


async def create_profile_item(
    session: AsyncSession,
    payload: ProfileItemCreateRequest,
) -> ProfileItem:
    item = ProfileItem(
        key=payload.key,
        type=payload.type,
        label=payload.label,
        value=payload.value,
        visibility=payload.visibility,
        source=payload.source,
        sort_order=payload.sort_order,
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def update_profile_item(
    session: AsyncSession,
    item: ProfileItem,
    payload: ProfileItemUpdateRequest,
) -> ProfileItem:
    item.key = payload.key
    item.type = payload.type
    item.label = payload.label
    item.value = payload.value
    item.visibility = payload.visibility
    item.source = payload.source
    item.sort_order = payload.sort_order
    await session.commit()
    await session.refresh(item)
    return item


async def delete_profile_item(session: AsyncSession, item: ProfileItem) -> None:
    await session.delete(item)
    await session.commit()
