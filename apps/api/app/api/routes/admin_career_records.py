from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import require_admin_user
from app.core.enums import CareerRecordType, Visibility
from app.db.models.user import User
from app.db.session import get_db_session
from app.schemas.career_records import (
    CareerRecordCreateRequest,
    CareerRecordResponse,
    CareerRecordUpdateRequest,
)
from app.services.career_records import (
    create_career_record,
    delete_career_record,
    get_career_record,
    list_career_records,
    update_career_record,
)

router = APIRouter(prefix="/api/admin/career-records", tags=["admin-career-records"])


@router.get("", response_model=list[CareerRecordResponse])
async def admin_list_career_records(
    visibility: Visibility | None = Query(default=None),
    record_type: CareerRecordType | None = Query(default=None),
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[CareerRecordResponse]:
    records = await list_career_records(
        session,
        visibility=visibility,
        record_type=record_type,
    )
    return [CareerRecordResponse.model_validate(record) for record in records]


@router.post("", response_model=CareerRecordResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_career_record(
    payload: CareerRecordCreateRequest,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> CareerRecordResponse:
    record = await create_career_record(session, payload)
    return CareerRecordResponse.model_validate(record)


@router.get("/{record_id}", response_model=CareerRecordResponse)
async def admin_get_career_record(
    record_id: int,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> CareerRecordResponse:
    record = await get_career_record(session, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Career record not found")

    return CareerRecordResponse.model_validate(record)


@router.put("/{record_id}", response_model=CareerRecordResponse)
async def admin_update_career_record(
    record_id: int,
    payload: CareerRecordUpdateRequest,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> CareerRecordResponse:
    record = await get_career_record(session, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Career record not found")

    updated = await update_career_record(session, record, payload)
    return CareerRecordResponse.model_validate(updated)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_career_record(
    record_id: int,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    record = await get_career_record(session, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Career record not found")

    await delete_career_record(session, record)
