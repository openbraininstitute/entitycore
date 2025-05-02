"""Merge branches

Revision ID: 7458f8ff53f0
Revises: b74f3ebacbca, a1b2c3d4e5f6
Create Date: 2025-05-02 08:24:05.134171

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = '7458f8ff53f0'
down_revision: Union[str, None] = ('b74f3ebacbca', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
