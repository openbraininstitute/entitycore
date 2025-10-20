"""empty message

Revision ID: e612f0d3ef18
Revises: bb07749764fc, c4f5577311e0
Create Date: 2025-10-20 09:22:38.619826

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "e612f0d3ef18"
down_revision: Union[str, None] = ("bb07749764fc", "c4f5577311e0")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
