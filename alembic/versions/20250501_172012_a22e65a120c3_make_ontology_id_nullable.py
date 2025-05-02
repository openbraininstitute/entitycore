"""Make ontology_id nullable

Revision ID: a22e65a120c3
Revises: abcd763b9bff
Create Date: 2025-05-01 17:20:12.941500

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "a22e65a120c3"
down_revision: Union[str, None] = "abcd763b9bff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("ion", "ontology_id", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    op.alter_column("ion", "ontology_id", existing_type=sa.String(), nullable=False)
