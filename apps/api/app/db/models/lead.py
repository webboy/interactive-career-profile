from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import EmailDeliveryStatus, LeadStatus
from app.db.base import Base
from app.db.types import pg_str_enum


class MeetingRequest(Base):
    __tablename__ = "meeting_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    requester_name: Mapped[str] = mapped_column(String(255), nullable=False)
    requester_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_times: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[LeadStatus] = mapped_column(
        pg_str_enum(LeadStatus, name="lead_status"),
        nullable=False,
        default=LeadStatus.NEW,
    )
    admin_email_status: Mapped[EmailDeliveryStatus] = mapped_column(
        pg_str_enum(EmailDeliveryStatus, name="email_delivery_status"),
        nullable=False,
        default=EmailDeliveryStatus.PENDING,
    )
    requester_email_status: Mapped[EmailDeliveryStatus] = mapped_column(
        pg_str_enum(EmailDeliveryStatus, name="email_delivery_status"),
        nullable=False,
        default=EmailDeliveryStatus.PENDING,
    )
    admin_email_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    requester_email_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class FollowUpRequest(Base):
    __tablename__ = "follow_up_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    requester_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[LeadStatus] = mapped_column(
        pg_str_enum(LeadStatus, name="lead_status"),
        nullable=False,
        default=LeadStatus.NEW,
    )
    admin_email_status: Mapped[EmailDeliveryStatus] = mapped_column(
        pg_str_enum(EmailDeliveryStatus, name="email_delivery_status"),
        nullable=False,
        default=EmailDeliveryStatus.PENDING,
    )
    requester_email_status: Mapped[EmailDeliveryStatus] = mapped_column(
        pg_str_enum(EmailDeliveryStatus, name="email_delivery_status"),
        nullable=False,
        default=EmailDeliveryStatus.PENDING,
    )
    admin_email_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    requester_email_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class JobSubmission(Base):
    __tablename__ = "job_submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    requester_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    job_description: Mapped[str] = mapped_column(Text, nullable=False)
    role_fit_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    retrieval_log_id: Mapped[int | None] = mapped_column(
        ForeignKey("retrieval_logs.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[LeadStatus] = mapped_column(
        pg_str_enum(LeadStatus, name="lead_status"),
        nullable=False,
        default=LeadStatus.NEW,
    )
    admin_email_status: Mapped[EmailDeliveryStatus] = mapped_column(
        pg_str_enum(EmailDeliveryStatus, name="email_delivery_status"),
        nullable=False,
        default=EmailDeliveryStatus.PENDING,
    )
    requester_email_status: Mapped[EmailDeliveryStatus] = mapped_column(
        pg_str_enum(EmailDeliveryStatus, name="email_delivery_status"),
        nullable=False,
        default=EmailDeliveryStatus.PENDING,
    )
    admin_email_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    requester_email_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
