"""replace derivationtype NULL by 'unspecified'

Revision ID: b97fadc73689
Revises: 317ec9e998d7
Create Date: 2025-09-12 12:36:03.355945

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "b97fadc73689"
down_revision: Union[str, None] = "317ec9e998d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # # Replace derivationtype NUll by 'unspecified'
    op.execute(
        "UPDATE derivation SET derivation_type = 'unspecified' WHERE derivation_type IS NULL"
    )
    # Set derivationtype to non nullable
    op.alter_column("derivation", "derivation_type", nullable=False)


def downgrade() -> None:
    # Set derivationtype back to nullable
    op.alter_column("derivation", "derivation_type", nullable=True, server_default=None)

    # Reset derivationtype 'unspecified' back to NULL
    op.execute("UPDATE derivation SET derivation_type = NULL WHERE derivation_type = 'unspecified'")
