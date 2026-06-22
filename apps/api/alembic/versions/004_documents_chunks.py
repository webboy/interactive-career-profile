"""Create documents and document_chunks tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "004_documents_chunks"
down_revision = "003_profile_career_records"
branch_labels = None
depends_on = None

document_source_type = postgresql.ENUM(
    "upload",
    "pasted_text",
    name="document_source_type",
    create_type=False,
)
document_file_type = postgresql.ENUM(
    "pdf",
    "docx",
    "txt",
    "markdown",
    "text",
    name="document_file_type",
    create_type=False,
)
document_visibility = postgresql.ENUM(
    "public",
    "private",
    "draft",
    "archived",
    name="document_visibility",
    create_type=False,
)
document_status = postgresql.ENUM(
    "uploaded",
    "extracted",
    "chunked",
    "failed",
    name="document_status",
    create_type=False,
)
document_embedding_status = postgresql.ENUM(
    "pending",
    "ready",
    "failed",
    "not_required",
    name="document_embedding_status",
    create_type=False,
)
document_chunk_visibility = postgresql.ENUM(
    "public",
    "private",
    "draft",
    "archived",
    name="document_chunk_visibility",
    create_type=False,
)
document_chunk_embedding_status = postgresql.ENUM(
    "pending",
    "ready",
    "failed",
    "not_required",
    name="document_chunk_embedding_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    document_source_type.create(bind, checkfirst=True)
    document_file_type.create(bind, checkfirst=True)
    document_visibility.create(bind, checkfirst=True)
    document_status.create(bind, checkfirst=True)
    document_embedding_status.create(bind, checkfirst=True)
    document_chunk_visibility.create(bind, checkfirst=True)
    document_chunk_embedding_status.create(bind, checkfirst=True)

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_type", document_source_type, nullable=False),
        sa.Column("file_type", document_file_type, nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("storage_path", sa.String(length=512), nullable=True),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("visibility", document_visibility, server_default="draft", nullable=False),
        sa.Column("status", document_status, server_default="uploaded", nullable=False),
        sa.Column("status_error", sa.Text(), nullable=True),
        sa.Column("embedding_status", document_embedding_status, server_default="pending", nullable=False),
        sa.Column("embedding_error", sa.Text(), nullable=True),
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
    op.create_index("ix_documents_status", "documents", ["status"], unique=False)
    op.create_index("ix_documents_visibility", "documents", ["visibility"], unique=False)

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("char_start", sa.Integer(), nullable=False),
        sa.Column("char_end", sa.Integer(), nullable=False),
        sa.Column("visibility", document_chunk_visibility, server_default="draft", nullable=False),
        sa.Column(
            "embedding_status",
            document_chunk_embedding_status,
            server_default="pending",
            nullable=False,
        ),
        sa.Column("embedding_error", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_document_chunks_document_id", table_name="document_chunks")
    op.drop_table("document_chunks")
    op.drop_index("ix_documents_visibility", table_name="documents")
    op.drop_index("ix_documents_status", table_name="documents")
    op.drop_table("documents")

    bind = op.get_bind()
    document_chunk_embedding_status.drop(bind, checkfirst=True)
    document_chunk_visibility.drop(bind, checkfirst=True)
    document_embedding_status.drop(bind, checkfirst=True)
    document_status.drop(bind, checkfirst=True)
    document_visibility.drop(bind, checkfirst=True)
    document_file_type.drop(bind, checkfirst=True)
    document_source_type.drop(bind, checkfirst=True)
