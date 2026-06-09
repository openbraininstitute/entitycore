"""merge_generic_result_and_main

Revision ID: 2dcd623d3e61
Revises: 267ed9485ccd, 696482acc02c
Create Date: 2026-06-09 13:21:08.682391

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "2dcd623d3e61"
down_revision: Union[str, None] = ("267ed9485ccd", "696482acc02c")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
