from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import CareerRecordType, EmbeddingStatus, Visibility


class CareerRecordCreateRequest(BaseModel):
    record_type: CareerRecordType
    title: str = Field(min_length=1, max_length=255)
    summary: str | None = None
    content: str = Field(min_length=1)
    visibility: Visibility = Visibility.PUBLIC
    source: str | None = Field(default=None, max_length=255)
    tags: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    sort_order: int = 0
    embedding_status: EmbeddingStatus = EmbeddingStatus.PENDING


class CareerRecordUpdateRequest(BaseModel):
    record_type: CareerRecordType
    title: str = Field(min_length=1, max_length=255)
    summary: str | None = None
    content: str = Field(min_length=1)
    visibility: Visibility
    source: str | None = Field(default=None, max_length=255)
    tags: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    sort_order: int = 0
    embedding_status: EmbeddingStatus
    embedding_error: str | None = None


class CareerRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    record_type: CareerRecordType
    title: str
    summary: str | None
    content: str
    visibility: Visibility
    source: str | None
    tags: str | None
    start_date: date | None
    end_date: date | None
    sort_order: int
    embedding_status: EmbeddingStatus
    embedding_error: str | None
    created_at: datetime
    updated_at: datetime
