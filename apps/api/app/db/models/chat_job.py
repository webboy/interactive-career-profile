from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import ChatJobStatus
from app.db.base import Base
from app.db.types import pg_str_enum


class ChatJob(Base):
    __tablename__ = "chat_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[ChatJobStatus] = mapped_column(
        pg_str_enum(ChatJobStatus, name="chat_job_status"),
        nullable=False,
        default=ChatJobStatus.QUEUED,
    )
    request_message: Mapped[str] = mapped_column(Text, nullable=False)
    request_language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    assistant_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    refused: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    grounded: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    sources_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
