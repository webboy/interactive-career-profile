from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import (
    DocumentFileType,
    DocumentSourceType,
    DocumentStatus,
    EmbeddingStatus,
    Visibility,
)


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source_type: DocumentSourceType
    file_type: DocumentFileType | None
    original_filename: str | None
    storage_path: str | None
    mime_type: str | None
    file_size_bytes: int | None
    extracted_text: str | None
    visibility: Visibility
    status: DocumentStatus
    status_error: str | None
    embedding_status: EmbeddingStatus
    embedding_error: str | None
    created_at: datetime
    updated_at: datetime


class DocumentTextCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    visibility: Visibility = Visibility.DRAFT


class DocumentUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    visibility: Visibility


class DocumentChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    chunk_index: int
    content: str
    char_start: int
    char_end: int
    visibility: Visibility
    embedding_status: EmbeddingStatus
    embedding_error: str | None
    created_at: datetime
    updated_at: datetime


class DocumentChunkUpdateRequest(BaseModel):
    visibility: Visibility


class DocumentIngestionActionResponse(BaseModel):
    document: DocumentResponse
    chunks_created: int | None = None
