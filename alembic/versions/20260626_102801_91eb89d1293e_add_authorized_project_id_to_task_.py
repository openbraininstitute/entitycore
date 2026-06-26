"""add_authorized_project_id_to_task_activity

Revision ID: 91eb89d1293e
Revises: a0357aa1c38b
Create Date: 2026-06-26 10:28:01.023843

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "91eb89d1293e"
down_revision: Union[str, None] = "a0357aa1c38b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("task_activity", sa.Column("authorized_project_id", sa.Uuid(), nullable=True))
    op.execute(
        """
        UPDATE task_activity ta
        SET authorized_project_id = a.authorized_project_id
        FROM activity a
        WHERE ta.id = a.id
        """
    )
    op.alter_column("task_activity", "authorized_project_id", nullable=False)
    op.create_index(
        op.f("ix_task_activity_authorized_project_id"),
        "task_activity",
        ["authorized_project_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_task_activity_authorized_project_id"), table_name="task_activity")
    op.drop_column("task_activity", "authorized_project_id")

