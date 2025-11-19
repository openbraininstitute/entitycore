"""Add notice_text

Revision ID: 0ce2b30e50d1
Revises: 4b526a1ded96
Create Date: 2025-11-18 17:30:10.650052

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "0ce2b30e50d1"
down_revision: Union[str, None] = "4b526a1ded96"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("scientific_artifact", sa.Column("notice_text", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("scientific_artifact", "notice_text")
