"""merge_generic_result_and_mesh_lod

Revision ID: 267ed9485ccd
Revises: a3f9c12b4e81, 42973a8b6a14
Create Date: 2026-06-09 12:54:54.735072

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "267ed9485ccd"
down_revision: Union[str, None] = ("a3f9c12b4e81", "42973a8b6a14")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
