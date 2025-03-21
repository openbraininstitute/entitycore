"""empty message

Revision ID: 652f1f3ffb80
Revises: c99dc0eb24b2
Create Date: 2025-03-18 12:09:08.206594

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "652f1f3ffb80"
down_revision: str | None = "c99dc0eb24b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "single_neuron_simulation",
        sa.Column("description_vector", postgresql.TSVECTOR(), nullable=True),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("single_neuron_simulation", "description_vector")
    # ### end Alembic commands ###
