from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CareerRecordType, Visibility
from app.db.models.career_record import CareerRecord
from app.schemas.career_records import CareerRecordCreateRequest, CareerRecordUpdateRequest


async def list_career_records(
    session: AsyncSession,
    visibility: Visibility | None = None,
    record_type: CareerRecordType | None = None,
) -> list[CareerRecord]:
    query = select(CareerRecord).order_by(CareerRecord.sort_order, CareerRecord.id)
    if visibility is not None:
        query = query.where(CareerRecord.visibility == visibility)
    if record_type is not None:
        query = query.where(CareerRecord.record_type == record_type)

    result = await session.execute(query)
    return list(result.scalars().all())


async def list_public_career_records(session: AsyncSession) -> list[CareerRecord]:
    return await list_career_records(session, visibility=Visibility.PUBLIC)


async def get_career_record(session: AsyncSession, record_id: int) -> CareerRecord | None:
    result = await session.execute(select(CareerRecord).where(CareerRecord.id == record_id))
    return result.scalar_one_or_none()


async def create_career_record(
    session: AsyncSession,
    payload: CareerRecordCreateRequest,
) -> CareerRecord:
    record = CareerRecord(
        record_type=payload.record_type,
        title=payload.title,
        summary=payload.summary,
        content=payload.content,
        visibility=payload.visibility,
        source=payload.source,
        tags=payload.tags,
        start_date=payload.start_date,
        end_date=payload.end_date,
        sort_order=payload.sort_order,
        embedding_status=payload.embedding_status,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def update_career_record(
    session: AsyncSession,
    record: CareerRecord,
    payload: CareerRecordUpdateRequest,
) -> CareerRecord:
    record.record_type = payload.record_type
    record.title = payload.title
    record.summary = payload.summary
    record.content = payload.content
    record.visibility = payload.visibility
    record.source = payload.source
    record.tags = payload.tags
    record.start_date = payload.start_date
    record.end_date = payload.end_date
    record.sort_order = payload.sort_order
    record.embedding_status = payload.embedding_status
    record.embedding_error = payload.embedding_error
    await session.commit()
    await session.refresh(record)
    return record


async def delete_career_record(session: AsyncSession, record: CareerRecord) -> None:
    await session.delete(record)
    await session.commit()
