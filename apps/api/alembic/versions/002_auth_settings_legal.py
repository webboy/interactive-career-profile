"""Create users, settings, and legal_pages tables."""

from alembic import op
import sqlalchemy as sa

revision = "002_auth_settings_legal"
down_revision = "001_pgvector_metadata"
branch_labels = None
depends_on = None

PRIVACY_PLACEHOLDER = """# Privacy Policy

This is placeholder privacy policy content for local development.

Public conversations and submitted contact details may be stored and reviewed by the profile owner.
"""

TERMS_PLACEHOLDER = """# Terms of Use

This is placeholder terms content for local development.

The assistant may be incomplete or incorrect and does not make binding hiring or employment commitments.
"""


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
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
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "settings",
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("is_secret", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("key"),
    )

    op.create_table(
        "legal_pages",
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("slug"),
    )

    legal_pages = sa.table(
        "legal_pages",
        sa.column("slug", sa.String),
        sa.column("title", sa.String),
        sa.column("content", sa.Text),
    )
    op.bulk_insert(
        legal_pages,
        [
            {
                "slug": "privacy",
                "title": "Privacy Policy",
                "content": PRIVACY_PLACEHOLDER,
            },
            {
                "slug": "terms",
                "title": "Terms of Use",
                "content": TERMS_PLACEHOLDER,
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("legal_pages")
    op.drop_table("settings")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
