"""add unspecified to derivationtype

Revision ID: 317ec9e998d7
Revises: de87a4c88ded
Create Date: 2025-09-12 11:56:08.832853

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "317ec9e998d7"
down_revision: Union[str, None] = "de87a4c88ded"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE derivationtype ADD VALUE IF NOT EXISTS 'unspecified'")


def downgrade() -> None:
    pass
    # # Set derivationtype back to nullable
    # op.alter_column("derivation", "derivation_type", nullable=True, server_default=None)

    # # Reset derivationtype 'unspecified' back to NULL
    # op.execute("UPDATE derivation SET derivation_type = NULL WHERE derivation_type = 'unspecified'")

    # # Replace NUll by 'unspecified'
    # op.execute(
    #     "UPDATE derivation SET derivation_type = 'unspecified' WHERE derivation_type IS NULL"
    # )
    # # Set derivationtype to non nullable
    # op.alter_column("derivation", "derivation_type", nullable=False)
