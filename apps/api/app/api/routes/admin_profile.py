from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import require_admin_user
from app.core.enums import Visibility
from app.db.models.user import User
from app.db.session import get_db_session
from app.schemas.profile import (
    ProfileItemCreateRequest,
    ProfileItemResponse,
    ProfileItemUpdateRequest,
)
from app.services.profile_items import (
    create_profile_item,
    delete_profile_item,
    get_profile_item,
    list_profile_items,
    update_profile_item,
)

router = APIRouter(prefix="/api/admin/profile-items", tags=["admin-profile"])


@router.get("", response_model=list[ProfileItemResponse])
async def admin_list_profile_items(
    visibility: Visibility | None = Query(default=None),
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[ProfileItemResponse]:
    items = await list_profile_items(session, visibility=visibility)
    return [ProfileItemResponse.model_validate(item) for item in items]


@router.post("", response_model=ProfileItemResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_profile_item(
    payload: ProfileItemCreateRequest,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> ProfileItemResponse:
    item = await create_profile_item(session, payload)
    return ProfileItemResponse.model_validate(item)


@router.get("/{item_id}", response_model=ProfileItemResponse)
async def admin_get_profile_item(
    item_id: int,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> ProfileItemResponse:
    item = await get_profile_item(session, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile item not found")

    return ProfileItemResponse.model_validate(item)


@router.put("/{item_id}", response_model=ProfileItemResponse)
async def admin_update_profile_item(
    item_id: int,
    payload: ProfileItemUpdateRequest,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> ProfileItemResponse:
    item = await get_profile_item(session, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile item not found")

    updated = await update_profile_item(session, item, payload)
    return ProfileItemResponse.model_validate(updated)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_profile_item(
    item_id: int,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    item = await get_profile_item(session, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile item not found")

    await delete_profile_item(session, item)
