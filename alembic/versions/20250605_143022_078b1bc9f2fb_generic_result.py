"""generic_result

Revision ID: <generate_a_new_hex_id>
Revises: f11898868755
Create Date: 2025-06-05 <current_time>

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

import app.db.types

# revision identifiers, used by Alembic.
revision: str = "<generate_a_new_hex_id>"
down_revision: Union[str, None] = "f11898868755"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "generic_result",
        sa.Column("id", sa.UUID(as_uuid=True), sa.ForeignKey("entity.id"), primary_key=True),
        sa.Column("result_type", sa.String(50), nullable=False),
        sa.Column("data_payload", sa.JSON, nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("description_vector", postgresql.TSVECTOR(), nullable=True),
    )
    op.create_index(
        "ix_generic_result_description_vector",
        "generic_result",
        ["description_vector"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(op.f("ix_generic_result_name"), "generic_result", ["name"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_generic_result_name"), table_name="generic_result")
    op.drop_index(
        "ix_generic_result_description_vector",
        table_name="generic_result",
        postgresql_using="gin",
    )
    op.drop_table("generic_result")
