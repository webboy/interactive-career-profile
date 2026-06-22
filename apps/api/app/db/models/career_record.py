from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import CareerRecordType, EmbeddingStatus, Visibility
from app.db.base import Base
from app.db.types import pg_str_enum


class CareerRecord(Base):
    __tablename__ = "career_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    record_type: Mapped[CareerRecordType] = mapped_column(
        pg_str_enum(CareerRecordType, name="career_record_type"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    visibility: Mapped[Visibility] = mapped_column(
        pg_str_enum(Visibility, name="career_record_visibility"),
        nullable=False,
        default=Visibility.PUBLIC,
    )
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    embedding_status: Mapped[EmbeddingStatus] = mapped_column(
        pg_str_enum(EmbeddingStatus, name="embedding_status"),
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
