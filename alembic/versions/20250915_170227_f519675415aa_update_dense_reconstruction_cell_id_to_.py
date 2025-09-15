"""Update dense_reconstruction_cell_id to bigint

Revision ID: f519675415aa
Revises: 06af11530839
Create Date: 2025-09-15 17:02:27.670044

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "f519675415aa"
down_revision: Union[str, None] = "06af11530839"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "em_cell_mesh",
        "dense_reconstruction_cell_id",
        existing_type=sa.INTEGER(),
        type_=sa.BigInteger(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "em_cell_mesh",
        "dense_reconstruction_cell_id",
        existing_type=sa.BigInteger(),
        type_=sa.INTEGER(),
        existing_nullable=False,
    )
