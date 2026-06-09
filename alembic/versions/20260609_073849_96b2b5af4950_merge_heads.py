"""merge_heads

Revision ID: 96b2b5af4950
Revises: 42973a8b6a14, 9fcb70c868ab
Create Date: 2026-06-09 07:38:49.560254

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "96b2b5af4950"
down_revision: Union[str, None] = ("42973a8b6a14", "9fcb70c868ab")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
