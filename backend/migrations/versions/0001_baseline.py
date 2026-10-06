"""baseline: the toDo schema as create_all leaves it

Revision ID: 0001
Revises:
Create Date: 2026-10-06 21:16:34.064640

The table, its two named CHECK constraints and the title index, byte for byte
as Base.metadata.create_all writes them on SQLite, and as every database made
before Alembic has them. Such a database is stamped at this revision, not
upgraded, after backend/migrations/check_baseline.py has accepted it.

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the toDo table and its title index."""
    op.create_table(
        "toDo",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted", sa.Boolean(), nullable=False),
        sa.Column("done", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("length(title) <= 255", name="title_length_check"),
        sa.CheckConstraint(
            "length(description) <= 255", name="description_length_check"
        ),
    )
    op.create_index(op.f("ix_toDo_title"), "toDo", ["title"], unique=False)


def downgrade() -> None:
    """Drop the title index and the toDo table."""
    op.drop_index(op.f("ix_toDo_title"), table_name="toDo")
    op.drop_table("toDo")
