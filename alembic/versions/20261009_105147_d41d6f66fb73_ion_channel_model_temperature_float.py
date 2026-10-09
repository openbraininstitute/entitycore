"""Ion channel model temperature float

Revision ID: d41d6f66fb73
Revises: 0d4ae0b8a312
Create Date: 2026-10-09 10:51:47.171683

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d41d6f66fb73"
down_revision: Union[str, None] = "0d4ae0b8a312"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "ion_channel_model",
        "temperature_celsius",
        existing_type=sa.INTEGER(),
        type_=sa.Float(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "ion_channel_model",
        "temperature_celsius",
        existing_type=sa.Float(),
        type_=sa.INTEGER(),
        existing_nullable=True,
        postgresql_using="round(temperature_celsius)::integer",
    )
