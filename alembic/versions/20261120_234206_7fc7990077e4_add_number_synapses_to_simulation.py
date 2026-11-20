"""Add number_synapses to Simulation

Revision ID: 7fc7990077e4
Revises: 48bdf29e1882
Create Date: 2026-11-20 23:42:06.803414

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from sqlalchemy import Text, text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "7fc7990077e4"
down_revision: Union[str, None] = "48bdf29e1882"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("simulation", sa.Column("number_synapses", sa.BigInteger(), nullable=True))

    # synapses were not counted before this column existed
    op.execute(text("UPDATE simulation SET number_synapses = 0"))

    op.alter_column("simulation", "number_synapses", nullable=False, server_default="0")


def downgrade() -> None:
    op.drop_column("simulation", "number_synapses")
