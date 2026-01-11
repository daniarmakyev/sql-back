"""add drafts table

Revision ID: 002_add_drafts
Revises: 001_initial
Create Date: 2024-01-11 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = "002_add_drafts"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "drafts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    # Create index on user_id for faster lookups
    op.create_index("ix_drafts_user_id", "drafts", ["user_id"])


def downgrade() -> None:
    # Use if_exists to avoid errors if index doesn't exist
    op.drop_index("ix_drafts_user_id", table_name="drafts", if_exists=True)
    op.drop_table("drafts")
