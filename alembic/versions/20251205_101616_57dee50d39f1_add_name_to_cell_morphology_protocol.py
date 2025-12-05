"""Add name to cell_morphology_protocol

Revision ID: 57dee50d39f1
Revises: f8366c8f0682
Create Date: 2025-12-05 10:16:16.970834

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "57dee50d39f1"
down_revision: Union[str, None] = "f8366c8f0682"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # add name and description with server_default="" to migrate existing records
    op.add_column(
        "cell_morphology_protocol",
        sa.Column("name", sa.String(), nullable=False, server_default=""),
    )
    op.add_column(
        "cell_morphology_protocol",
        sa.Column("description", sa.String(), nullable=False, server_default=""),
    )
    # remove server_default from name and description for consistency with the other tables
    op.alter_column(
        "cell_morphology_protocol", "name", existing_type=sa.String(), server_default=None
    )
    op.alter_column(
        "cell_morphology_protocol", "description", existing_type=sa.String(), server_default=None
    )
    # add description_vector and indexes
    op.add_column(
        "cell_morphology_protocol",
        sa.Column("description_vector", postgresql.TSVECTOR(), nullable=True),
    )
    op.create_index(
        "ix_cell_morphology_protocol_description_vector",
        "cell_morphology_protocol",
        ["description_vector"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        op.f("ix_cell_morphology_protocol_name"), "cell_morphology_protocol", ["name"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_cell_morphology_protocol_name"), table_name="cell_morphology_protocol")
    op.drop_index(
        "ix_cell_morphology_protocol_description_vector",
        table_name="cell_morphology_protocol",
        postgresql_using="gin",
    )
    op.drop_column("cell_morphology_protocol", "description_vector")
    op.drop_column("cell_morphology_protocol", "description")
    op.drop_column("cell_morphology_protocol", "name")
