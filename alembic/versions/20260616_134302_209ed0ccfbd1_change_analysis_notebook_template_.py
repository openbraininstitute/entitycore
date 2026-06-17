"""change analysis notebook template exercise_id to string

Revision ID: 209ed0ccfbd1
Revises: c9d905433b3e
Create Date: 2026-06-16 13:43:02.280256

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


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
    conn = op.get_bind()
    bad = conn.execute(
        sa.text(
            "SELECT COUNT(*) FROM analysis_notebook_template "
            "WHERE exercise_id IS NOT NULL AND exercise_id !~* "
            "'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'"
        )
    ).scalar()
    if bad:
        raise RuntimeError(f"Cannot downgrade: {bad} exercise_id value(s) are not valid UUIDs")
    op.alter_column(
        "analysis_notebook_template",
        "exercise_id",
        existing_type=sa.String(length=255),
        type_=sa.Uuid(),
        existing_nullable=True,
        postgresql_using="exercise_id::uuid",
    )
