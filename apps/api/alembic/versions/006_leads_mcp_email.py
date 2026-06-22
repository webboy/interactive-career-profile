"""Add lead persistence tables for MCP email workflows."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "006_leads_mcp_email"
down_revision = "005_hybrid_retrieval_logging"
branch_labels = None
depends_on = None

lead_status = postgresql.ENUM("new", "sent", "failed", "reviewed", name="lead_status", create_type=False)
email_delivery_status = postgresql.ENUM(
    "not_required",
    "pending",
    "sent",
    "failed",
    name="email_delivery_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    lead_status.create(bind, checkfirst=True)
    email_delivery_status.create(bind, checkfirst=True)

    op.create_table(
        "meeting_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("requester_name", sa.String(length=255), nullable=False),
        sa.Column("requester_email", sa.String(length=255), nullable=False),
        sa.Column("organization", sa.String(length=255), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("preferred_times", sa.Text(), nullable=True),
        sa.Column("status", lead_status, nullable=False, server_default="new"),
        sa.Column("admin_email_status", email_delivery_status, nullable=False, server_default="pending"),
        sa.Column("requester_email_status", email_delivery_status, nullable=False, server_default="pending"),
        sa.Column("admin_email_error", sa.Text(), nullable=True),
        sa.Column("requester_email_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_meeting_requests_requester_email", "meeting_requests", ["requester_email"], unique=False)

    op.create_table(
        "follow_up_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("requester_email", sa.String(length=255), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("status", lead_status, nullable=False, server_default="new"),
        sa.Column("admin_email_status", email_delivery_status, nullable=False, server_default="pending"),
        sa.Column("requester_email_status", email_delivery_status, nullable=False, server_default="pending"),
        sa.Column("admin_email_error", sa.Text(), nullable=True),
        sa.Column("requester_email_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_follow_up_requests_requester_email", "follow_up_requests", ["requester_email"], unique=False)

    op.create_table(
        "job_submissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("requester_email", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column("role_title", sa.String(length=255), nullable=True),
        sa.Column("job_description", sa.Text(), nullable=False),
        sa.Column("role_fit_summary", sa.Text(), nullable=True),
        sa.Column("retrieval_log_id", sa.Integer(), nullable=True),
        sa.Column("status", lead_status, nullable=False, server_default="new"),
        sa.Column("admin_email_status", email_delivery_status, nullable=False, server_default="pending"),
        sa.Column("requester_email_status", email_delivery_status, nullable=False, server_default="pending"),
        sa.Column("admin_email_error", sa.Text(), nullable=True),
        sa.Column("requester_email_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["retrieval_log_id"], ["retrieval_logs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_submissions_requester_email", "job_submissions", ["requester_email"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_job_submissions_requester_email", table_name="job_submissions")
    op.drop_table("job_submissions")
    op.drop_index("ix_follow_up_requests_requester_email", table_name="follow_up_requests")
    op.drop_table("follow_up_requests")
    op.drop_index("ix_meeting_requests_requester_email", table_name="meeting_requests")
    op.drop_table("meeting_requests")
    email_delivery_status.drop(op.get_bind(), checkfirst=True)
    lead_status.drop(op.get_bind(), checkfirst=True)
