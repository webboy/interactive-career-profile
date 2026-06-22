"""Add document chunk embeddings and hybrid retrieval logging tables."""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision = "005_hybrid_retrieval_logging"
down_revision = "004_documents_chunks"
branch_labels = None
depends_on = None

message_role = postgresql.ENUM("user", "assistant", "system", name="message_role", create_type=False)
tool_call_status = postgresql.ENUM(
    "pending",
    "success",
    "failed",
    name="tool_call_status",
    create_type=False,
)
source_category = postgresql.ENUM(
    "profile_item",
    "career_record",
    "document_chunk",
    name="source_category",
    create_type=False,
)
retrieval_log_visibility = postgresql.ENUM(
    "public",
    "private",
    "draft",
    "archived",
    name="retrieval_log_visibility",
    create_type=False,
)
unanswered_prompt_reason = postgresql.ENUM(
    "no_context",
    "below_threshold",
    "policy",
    "other",
    name="unanswered_prompt_reason",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    message_role.create(bind, checkfirst=True)
    tool_call_status.create(bind, checkfirst=True)
    source_category.create(bind, checkfirst=True)
    retrieval_log_visibility.create(bind, checkfirst=True)
    unanswered_prompt_reason.create(bind, checkfirst=True)

    op.add_column("document_chunks", sa.Column("embedding", Vector(1536), nullable=True))

    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("language", sa.String(length=32), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversations_session_id", "conversations", ["session_id"], unique=False)

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("role", message_role, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"], unique=False)

    op.create_table(
        "tool_calls",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("tool_name", sa.String(length=255), nullable=False),
        sa.Column("status", tool_call_status, server_default="pending", nullable=False),
        sa.Column("request_payload", sa.Text(), nullable=True),
        sa.Column("response_payload", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tool_calls_conversation_id", "tool_calls", ["conversation_id"], unique=False)

    op.create_table(
        "retrieval_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=32), nullable=True),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("structured_limit", sa.Integer(), nullable=False),
        sa.Column("document_limit", sa.Integer(), nullable=False),
        sa.Column("document_score_threshold", sa.Float(), nullable=False),
        sa.Column("had_usable_context", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "retrieval_log_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("retrieval_log_id", sa.Integer(), nullable=False),
        sa.Column("source_type", source_category, nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("snippet", sa.Text(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("visibility", retrieval_log_visibility, nullable=False),
        sa.Column("was_used", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("precedence_rank", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["retrieval_log_id"], ["retrieval_logs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_retrieval_log_items_retrieval_log_id",
        "retrieval_log_items",
        ["retrieval_log_id"],
        unique=False,
    )

    op.create_table(
        "unanswered_prompts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("reason", unanswered_prompt_reason, nullable=False),
        sa.Column("language", sa.String(length=32), nullable=True),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("retrieval_log_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["retrieval_log_id"], ["retrieval_logs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_unanswered_prompts_retrieval_log_id",
        "unanswered_prompts",
        ["retrieval_log_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_unanswered_prompts_retrieval_log_id", table_name="unanswered_prompts")
    op.drop_table("unanswered_prompts")
    op.drop_index("ix_retrieval_log_items_retrieval_log_id", table_name="retrieval_log_items")
    op.drop_table("retrieval_log_items")
    op.drop_table("retrieval_logs")
    op.drop_index("ix_tool_calls_conversation_id", table_name="tool_calls")
    op.drop_table("tool_calls")
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")
    op.drop_index("ix_conversations_session_id", table_name="conversations")
    op.drop_table("conversations")
    op.drop_column("document_chunks", "embedding")

    bind = op.get_bind()
    unanswered_prompt_reason.drop(bind, checkfirst=True)
    retrieval_log_visibility.drop(bind, checkfirst=True)
    source_category.drop(bind, checkfirst=True)
    tool_call_status.drop(bind, checkfirst=True)
    message_role.drop(bind, checkfirst=True)
