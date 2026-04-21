"""unique cell_morpholy_protocol name

Revision ID: 2f5c75357494
Revises: f4744cf2307b
Create Date: 2026-04-20 18:25:46.370808

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "2f5c75357494"
down_revision: Union[str, None] = "f4744cf2307b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f("ix_cell_morphology_protocol_name"), table_name="cell_morphology_protocol")
    # it can fail if there are multiple protocols with the same name
    op.create_index(
        op.f("ix_cell_morphology_protocol_name"), "cell_morphology_protocol", ["name"], unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_cell_morphology_protocol_name"), table_name="cell_morphology_protocol")
    op.create_index(
        op.f("ix_cell_morphology_protocol_name"), "cell_morphology_protocol", ["name"], unique=False
    )
