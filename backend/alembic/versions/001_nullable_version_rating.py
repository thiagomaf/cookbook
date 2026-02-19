"""Make recipe_versions.rating nullable

Revision ID: 001
Revises:
Create Date: 2026-02-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite requires batch mode to alter column nullability
    with op.batch_alter_table("recipe_versions") as batch_op:
        batch_op.alter_column(
            "rating",
            existing_type=sa.Integer(),
            nullable=True,
        )


def downgrade() -> None:
    # Restore NOT NULL — set any NULLs to 0 first to avoid constraint violation
    op.execute("UPDATE recipe_versions SET rating = 0 WHERE rating IS NULL")
    with op.batch_alter_table("recipe_versions") as batch_op:
        batch_op.alter_column(
            "rating",
            existing_type=sa.Integer(),
            nullable=False,
        )
