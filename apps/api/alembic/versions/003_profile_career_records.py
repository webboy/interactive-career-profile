"""Create profile_items and career_records tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003_profile_career_records"
down_revision = "002_auth_settings_legal"
branch_labels = None
depends_on = None

profile_item_type = postgresql.ENUM(
    "text",
    "link",
    "email",
    "location",
    "language",
    "availability",
    "other",
    name="profile_item_type",
    create_type=False,
)
visibility = postgresql.ENUM(
    "public",
    "private",
    "draft",
    "archived",
    name="visibility",
    create_type=False,
)
career_record_type = postgresql.ENUM(
    "experience",
    "project",
    "skill",
    "education",
    "certification",
    "language",
    "achievement",
    "leadership",
    "availability",
    "other",
    name="career_record_type",
    create_type=False,
)
career_record_visibility = postgresql.ENUM(
    "public",
    "private",
    "draft",
    "archived",
    name="career_record_visibility",
    create_type=False,
)
embedding_status = postgresql.ENUM(
    "pending",
    "ready",
    "failed",
    "not_required",
    name="embedding_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    profile_item_type.create(bind, checkfirst=True)
    visibility.create(bind, checkfirst=True)
    career_record_type.create(bind, checkfirst=True)
    career_record_visibility.create(bind, checkfirst=True)
    embedding_status.create(bind, checkfirst=True)

    op.create_table(
        "profile_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("type", profile_item_type, nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("visibility", visibility, server_default="private", nullable=False),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
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
    op.create_index("ix_profile_items_key", "profile_items", ["key"], unique=False)

    op.create_table(
        "career_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("record_type", career_record_type, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("visibility", career_record_visibility, server_default="public", nullable=False),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("embedding_status", embedding_status, server_default="pending", nullable=False),
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
    op.create_index("ix_career_records_record_type", "career_records", ["record_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_career_records_record_type", table_name="career_records")
    op.drop_table("career_records")
    op.drop_index("ix_profile_items_key", table_name="profile_items")
    op.drop_table("profile_items")

    bind = op.get_bind()
    embedding_status.drop(bind, checkfirst=True)
    career_record_visibility.drop(bind, checkfirst=True)
    career_record_type.drop(bind, checkfirst=True)
    visibility.drop(bind, checkfirst=True)
    profile_item_type.drop(bind, checkfirst=True)
