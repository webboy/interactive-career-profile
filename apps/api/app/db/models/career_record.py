from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import CareerRecordType, EmbeddingStatus, Visibility
from app.db.base import Base


class CareerRecord(Base):
    __tablename__ = "career_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    record_type: Mapped[CareerRecordType] = mapped_column(
        Enum(CareerRecordType, name="career_record_type"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    visibility: Mapped[Visibility] = mapped_column(
        Enum(Visibility, name="career_record_visibility"),
        nullable=False,
        default=Visibility.PUBLIC,
    )
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    embedding_status: Mapped[EmbeddingStatus] = mapped_column(
        Enum(EmbeddingStatus, name="embedding_status"),
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
