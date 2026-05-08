"""Add label column to derivation and emodel_circuit DerivationType

Revision ID: 1caa2fc3d44e
Revises: c8cdf20bbb0d
Create Date: 2026-05-08 06:30:47.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from alembic_postgresql_enum import TableReference

import app.db.types

# revision identifiers, used by Alembic.
revision: str = "1caa2fc3d44e"
down_revision: Union[str, None] = "c8cdf20bbb0d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add nullable label column to derivation table.
    op.add_column("derivation", sa.Column("label", sa.String(), nullable=True))

    # Extend DerivationType enum with emodel_circuit.
    op.sync_enum_values(
        enum_schema="public",
        enum_name="derivationtype",
        new_values=["circuit_extraction", "circuit_rewiring", "emodel_circuit", "unspecified"],
        affected_columns=[
            TableReference(
                table_schema="public", table_name="derivation", column_name="derivation_type"
            )
        ],
        enum_values_to_rename=[],
    )


def downgrade() -> None:
    op.sync_enum_values(
        enum_schema="public",
        enum_name="derivationtype",
        new_values=["circuit_extraction", "circuit_rewiring", "unspecified"],
        affected_columns=[
            TableReference(
                table_schema="public", table_name="derivation", column_name="derivation_type"
            )
        ],
        enum_values_to_rename=[],
    )
    op.drop_column("derivation", "label")
