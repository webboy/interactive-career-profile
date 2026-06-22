from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import (
    DocumentFileType,
    DocumentSourceType,
    DocumentStatus,
    EmbeddingStatus,
    Visibility,
)
from app.db.base import Base
from app.db.types import EmbeddingVector, pg_str_enum


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[DocumentSourceType] = mapped_column(
        pg_str_enum(DocumentSourceType, name="document_source_type"),
        nullable=False,
    )
    file_type: Mapped[DocumentFileType | None] = mapped_column(
        pg_str_enum(DocumentFileType, name="document_file_type"),
        nullable=True,
    )
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    storage_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[Visibility] = mapped_column(
        pg_str_enum(Visibility, name="document_visibility"),
        nullable=False,
        default=Visibility.DRAFT,
    )
    status: Mapped[DocumentStatus] = mapped_column(
        pg_str_enum(DocumentStatus, name="document_status"),
        nullable=False,
        default=DocumentStatus.UPLOADED,
    )
    status_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_status: Mapped[EmbeddingStatus] = mapped_column(
        pg_str_enum(EmbeddingStatus, name="document_embedding_status"),
        nullable=False,
        default=EmbeddingStatus.PENDING,
    )
    embedding_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    visibility: Mapped[Visibility] = mapped_column(
        pg_str_enum(Visibility, name="document_chunk_visibility"),
        nullable=False,
        default=Visibility.DRAFT,
    )
    embedding_status: Mapped[EmbeddingStatus] = mapped_column(
        pg_str_enum(EmbeddingStatus, name="document_chunk_embedding_status"),
        nullable=False,
        default=EmbeddingStatus.PENDING,
    )
    embedding_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(EmbeddingVector(1536), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
