"""Enable pgvector and create system metadata table."""

from alembic import op
import sqlalchemy as sa

revision = "001_pgvector_metadata"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "system_metadata",
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("value", sa.String(length=255), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("key"),
    )
    op.execute(
        """
        INSERT INTO system_metadata (key, value)
        VALUES ('api_version', '0.0.1')
        """
    )


def downgrade() -> None:
    op.drop_table("system_metadata")
    op.execute("DROP EXTENSION IF EXISTS vector")
