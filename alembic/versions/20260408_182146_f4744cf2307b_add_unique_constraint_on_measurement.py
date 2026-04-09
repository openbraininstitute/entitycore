"""Add unique constraint on measurement

Revision ID: f4744cf2307b
Revises: 3ba5873875fa
Create Date: 2026-04-08 18:21:46.492575

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "f4744cf2307b"
down_revision: Union[str, None] = "3ba5873875fa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_measurement_entity_id_name",
        "measurement_record",
        ["entity_id", "name"],
        deferrable=True,
        initially="deferred",
    )


def downgrade() -> None:
    op.drop_constraint("uq_measurement_entity_id_name", "measurement_record", type_="unique")
