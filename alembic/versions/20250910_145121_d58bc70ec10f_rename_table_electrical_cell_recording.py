"""Rename table electrical_cell_recording to electrical_recording

Revision ID: d58bc70ec10f
Revises: 9df9950d73a0
Create Date: 2025-09-10 14:51:21.492590

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from alembic_postgresql_enum import TableReference
from sqlalchemy.dialects import postgresql

from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "d58bc70ec10f"
down_revision: Union[str, None] = "9df9950d73a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("electrical_cell_recording", "electrical_recording")
    op.execute("ALTER INDEX pk_electrical_cell_recording RENAME TO pk_electrical_recording")


def downgrade() -> None:
    op.rename_table("electrical_recording", "electrical_cell_recording")
    op.execute("ALTER INDEX pk_electrical_recording RENAME TO pk_electrical_cell_recording")
