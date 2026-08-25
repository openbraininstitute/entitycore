"""add uuid-ossp

Revision ID: 8953d8ad7437
Revises: 5b0ea9253ea5
Create Date: 2026-08-17 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
from alembic_utils.pg_extension import PGExtension

# revision identifiers, used by Alembic.
revision: str = "8953d8ad7437"
down_revision: Union[str, None] = "5b0ea9253ea5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    public_vector = PGExtension(schema="public", signature="uuid-ossp")
    op.create_entity(public_vector)


def downgrade() -> None:
    public_vector = PGExtension(schema="public", signature="uuid-ossp")
    op.drop_entity(public_vector)
