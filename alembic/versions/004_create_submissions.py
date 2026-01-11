"""create submissions table

Revision ID: 004_create_submissions
Revises: 003_update_challenges_schema
Create Date: 2024-01-11 14:45:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = "004_create_submissions"
down_revision = "003_update_challenges_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if submissions table exists
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()

    if "submissions" not in tables:
        op.create_table(
            "submissions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("challenge_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("query", sa.Text(), nullable=False),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("passed_tests", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_tests", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("execution_time", sa.Float(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column(
                "test_results", postgresql.JSON(astext_type=sa.Text()), nullable=True
            ),
            sa.Column(
                "submitted_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        # Create indexes for better query performance
        op.create_index("ix_submissions_challenge_id", "submissions", ["challenge_id"])
        op.create_index("ix_submissions_user_id", "submissions", ["user_id"])
        op.create_index("ix_submissions_status", "submissions", ["status"])
    else:
        # Table exists, check and create missing indexes
        indexes = [idx["name"] for idx in inspector.get_indexes("submissions")]
        if "ix_submissions_challenge_id" not in indexes:
            op.create_index(
                "ix_submissions_challenge_id", "submissions", ["challenge_id"]
            )
        if "ix_submissions_user_id" not in indexes:
            op.create_index("ix_submissions_user_id", "submissions", ["user_id"])
        if "ix_submissions_status" not in indexes:
            op.create_index("ix_submissions_status", "submissions", ["status"])


def downgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    # Check and drop indexes if they exist
    if "submissions" in inspector.get_table_names():
        indexes = [idx["name"] for idx in inspector.get_indexes("submissions")]
        if "ix_submissions_status" in indexes:
            op.drop_index("ix_submissions_status", table_name="submissions")
        if "ix_submissions_user_id" in indexes:
            op.drop_index("ix_submissions_user_id", table_name="submissions")
        if "ix_submissions_challenge_id" in indexes:
            op.drop_index("ix_submissions_challenge_id", table_name="submissions")

        op.drop_table("submissions")
