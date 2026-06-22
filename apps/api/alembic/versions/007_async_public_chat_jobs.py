"""Add async public chat job persistence."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "007_async_public_chat_jobs"
down_revision = "006_leads_mcp_email"
branch_labels = None
depends_on = None

chat_job_status = postgresql.ENUM(
    "queued",
    "processing",
    "completed",
    "failed",
    name="chat_job_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    chat_job_status.create(bind, checkfirst=True)

    op.create_table(
        "chat_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=255), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("status", chat_job_status, nullable=False, server_default="queued"),
        sa.Column("request_message", sa.Text(), nullable=False),
        sa.Column("request_language", sa.String(length=32), nullable=True),
        sa.Column("assistant_message", sa.Text(), nullable=True),
        sa.Column("response_language", sa.String(length=32), nullable=True),
        sa.Column("refused", sa.Boolean(), nullable=True),
        sa.Column("grounded", sa.Boolean(), nullable=True),
        sa.Column("sources_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_jobs_conversation_id", "chat_jobs", ["conversation_id"], unique=False)
    op.create_index("ix_chat_jobs_session_id", "chat_jobs", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_chat_jobs_session_id", table_name="chat_jobs")
    op.drop_index("ix_chat_jobs_conversation_id", table_name="chat_jobs")
    op.drop_table("chat_jobs")
    chat_job_status.drop(op.get_bind(), checkfirst=True)
