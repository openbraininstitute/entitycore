"""change analysis notebook template exercise_id to string

Revision ID: 209ed0ccfbd1
Revises: c9d905433b3e
Create Date: 2026-06-16 13:43:02.280256

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "209ed0ccfbd1"
down_revision: Union[str, None] = "c9d905433b3e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "analysis_notebook_template",
        "exercise_id",
        existing_type=sa.Uuid(),
        type_=sa.String(length=255),
        existing_nullable=True,
        postgresql_using="exercise_id::text",
    )


def downgrade() -> None:
    op.alter_column(
        "analysis_notebook_template",
        "exercise_id",
        existing_type=sa.String(length=255),
        type_=sa.Uuid(),
        existing_nullable=True,
        postgresql_using="exercise_id::uuid",
    )
