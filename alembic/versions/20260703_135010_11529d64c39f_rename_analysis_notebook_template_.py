"""rename analysis notebook template exercise_id to assignment_id

Revision ID: 11529d64c39f
Revises: b26853460669
Create Date: 2026-07-03 13:50:10.326074

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "11529d64c39f"
down_revision: Union[str, None] = "b26853460669"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "analysis_notebook_template",
        "exercise_id",
        new_column_name="assignment_id",
        existing_type=sa.String(length=255),
        existing_nullable=True,
    )
    op.execute(
        "ALTER INDEX ix_analysis_notebook_template_exercise_id "
        "RENAME TO ix_analysis_notebook_template_assignment_id"
    )


def downgrade() -> None:
    op.execute(
        "ALTER INDEX ix_analysis_notebook_template_assignment_id "
        "RENAME TO ix_analysis_notebook_template_exercise_id"
    )
    op.alter_column(
        "analysis_notebook_template",
        "assignment_id",
        new_column_name="exercise_id",
        existing_type=sa.String(length=255),
        existing_nullable=True,
    )
