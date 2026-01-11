"""update challenges schema

Revision ID: 003_update_challenges_schema
Revises: 002_add_drafts
Create Date: 2024-01-11 14:40:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = "003_update_challenges_schema"
down_revision = "002_add_drafts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check and drop old columns if they exist
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col["name"] for col in inspector.get_columns("challenges")]

    if "question" in columns:
        op.drop_column("challenges", "question")
    if "correct_answer" in columns:
        op.drop_column("challenges", "correct_answer")
    if "user_answer" in columns:
        op.drop_column("challenges", "user_answer")
    if "is_correct" in columns:
        op.drop_column("challenges", "is_correct")

    # Add new columns if they don't exist
    if "title" not in columns:
        op.add_column(
            "challenges",
            sa.Column(
                "title", sa.String(255), nullable=False, server_default="Untitled"
            ),
        )
        op.alter_column("challenges", "title", server_default=None)

    if "description" not in columns:
        op.add_column(
            "challenges",
            sa.Column(
                "description",
                sa.Text(),
                nullable=False,
                server_default="No description",
            ),
        )
        op.alter_column("challenges", "description", server_default=None)

    if "topics" not in columns:
        op.add_column(
            "challenges",
            sa.Column(
                "topics",
                postgresql.JSON(astext_type=sa.Text()),
                nullable=False,
                server_default="[]",
            ),
        )
        op.alter_column("challenges", "topics", server_default=None)

    if "schema_definition" not in columns:
        op.add_column(
            "challenges",
            sa.Column(
                "schema_definition",
                postgresql.JSON(astext_type=sa.Text()),
                nullable=False,
                server_default="{}",
            ),
        )
        op.alter_column("challenges", "schema_definition", server_default=None)

    if "sample_data" not in columns:
        op.add_column(
            "challenges",
            sa.Column(
                "sample_data",
                postgresql.JSON(astext_type=sa.Text()),
                nullable=False,
                server_default="{}",
            ),
        )
        op.alter_column("challenges", "sample_data", server_default=None)

    if "expected_output" not in columns:
        op.add_column(
            "challenges",
            sa.Column(
                "expected_output",
                postgresql.JSON(astext_type=sa.Text()),
                nullable=False,
                server_default="[]",
            ),
        )
        op.alter_column("challenges", "expected_output", server_default=None)

    if "solution_query" not in columns:
        op.add_column(
            "challenges",
            sa.Column(
                "solution_query", sa.Text(), nullable=False, server_default="SELECT 1"
            ),
        )
        op.alter_column("challenges", "solution_query", server_default=None)

    if "test_cases" not in columns:
        op.add_column(
            "challenges",
            sa.Column(
                "test_cases",
                postgresql.JSON(astext_type=sa.Text()),
                nullable=False,
                server_default="[]",
            ),
        )
        op.alter_column("challenges", "test_cases", server_default=None)

    if "hints" not in columns:
        op.add_column(
            "challenges",
            sa.Column("hints", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        )

    if "user_id" not in columns:
        op.add_column(
            "challenges",
            sa.Column("user_id", sa.Integer(), nullable=False, server_default="1"),
        )
        op.alter_column("challenges", "user_id", server_default=None)


def downgrade() -> None:
    # Check and drop new columns if they exist
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col["name"] for col in inspector.get_columns("challenges")]

    if "user_id" in columns:
        op.drop_column("challenges", "user_id")
    if "hints" in columns:
        op.drop_column("challenges", "hints")
    if "test_cases" in columns:
        op.drop_column("challenges", "test_cases")
    if "solution_query" in columns:
        op.drop_column("challenges", "solution_query")
    if "expected_output" in columns:
        op.drop_column("challenges", "expected_output")
    if "sample_data" in columns:
        op.drop_column("challenges", "sample_data")
    if "schema_definition" in columns:
        op.drop_column("challenges", "schema_definition")
    if "topics" in columns:
        op.drop_column("challenges", "topics")
    if "description" in columns:
        op.drop_column("challenges", "description")
    if "title" in columns:
        op.drop_column("challenges", "title")

    # Add back old columns if they don't exist
    if "question" not in columns:
        op.add_column(
            "challenges",
            sa.Column("question", sa.Text(), nullable=False, server_default=""),
        )
    if "correct_answer" not in columns:
        op.add_column(
            "challenges",
            sa.Column("correct_answer", sa.Text(), nullable=False, server_default=""),
        )
    if "user_answer" not in columns:
        op.add_column("challenges", sa.Column("user_answer", sa.Text(), nullable=True))
    if "is_correct" not in columns:
        op.add_column(
            "challenges", sa.Column("is_correct", sa.Boolean(), nullable=True)
        )
