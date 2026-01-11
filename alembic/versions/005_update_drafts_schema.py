"""update drafts schema

Revision ID: 005_update_drafts_schema
Revises: 004_create_submissions
Create Date: 2024-01-11 14:50:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = "005_update_drafts_schema"
down_revision = "004_create_submissions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if drafts table exists and what columns it has
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if "drafts" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("drafts")]

        # Add challenge_id column if it doesn't exist
        if "challenge_id" not in columns:
            op.add_column(
                "drafts",
                sa.Column(
                    "challenge_id", sa.Integer(), nullable=False, server_default="0"
                ),
            )
            op.alter_column("drafts", "challenge_id", server_default=None)

        # Ensure created_at exists (rename query to created_at if needed, or just add it)
        if "created_at" not in columns:
            op.execute(
                "ALTER TABLE drafts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            )


def downgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if "drafts" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("drafts")]

        if "challenge_id" in columns:
            op.drop_column("drafts", "challenge_id")

        if "created_at" in columns:
            op.execute("ALTER TABLE drafts DROP COLUMN IF EXISTS created_at")
