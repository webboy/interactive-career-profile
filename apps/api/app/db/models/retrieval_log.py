from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import SourceCategory, UnansweredPromptReason, Visibility
from app.db.base import Base
from app.db.types import pg_str_enum


class RetrievalLog(Base):
    __tablename__ = "retrieval_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    structured_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    document_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    document_score_threshold: Mapped[float] = mapped_column(Float, nullable=False)
    had_usable_context: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    items: Mapped[list["RetrievalLogItem"]] = relationship(
        "RetrievalLogItem",
        back_populates="retrieval_log",
        cascade="all, delete-orphan",
    )
    unanswered_prompts: Mapped[list["UnansweredPrompt"]] = relationship(
        "UnansweredPrompt",
        back_populates="retrieval_log",
    )


class RetrievalLogItem(Base):
    __tablename__ = "retrieval_log_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    retrieval_log_id: Mapped[int] = mapped_column(
        ForeignKey("retrieval_logs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type: Mapped[SourceCategory] = mapped_column(
        pg_str_enum(SourceCategory, name="source_category"),
        nullable=False,
    )
    source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    snippet: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    visibility: Mapped[Visibility] = mapped_column(
        pg_str_enum(Visibility, name="retrieval_log_visibility"),
        nullable=False,
    )
    was_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    precedence_rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    retrieval_log: Mapped["RetrievalLog"] = relationship("RetrievalLog", back_populates="items")


class UnansweredPrompt(Base):
    __tablename__ = "unanswered_prompts"

    id: Mapped[int] = mapped_column(primary_key=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[UnansweredPromptReason] = mapped_column(
        pg_str_enum(UnansweredPromptReason, name="unanswered_prompt_reason"),
        nullable=False,
    )
    language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    retrieval_log_id: Mapped[int | None] = mapped_column(
        ForeignKey("retrieval_logs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    retrieval_log: Mapped["RetrievalLog | None"] = relationship(
        "RetrievalLog",
        back_populates="unanswered_prompts",
    )
