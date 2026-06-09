"""merge_generic_result_and_mesh_lod

Revision ID: 9fcb70c868ab
Revises: a3f9c12b4e81, 22ff1f757742
Create Date: 2026-06-09 07:25:15.684938

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "9fcb70c868ab"
down_revision: Union[str, None] = ("a3f9c12b4e81", "22ff1f757742")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
