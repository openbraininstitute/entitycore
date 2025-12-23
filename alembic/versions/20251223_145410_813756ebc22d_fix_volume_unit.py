"""Fix volume unit

Revision ID: 813756ebc22d
Revises: 3f43728354a6
Create Date: 2025-12-23 14:54:10.403860

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from alembic_postgresql_enum import TableReference

from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "813756ebc22d"
down_revision: Union[str, None] = "3f43728354a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _migrate_data() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            UPDATE measurement_item
            SET unit = 'volume__um3'
            WHERE unit = 'volume__mm3'
        """)
    )


def _revert_data() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            UPDATE measurement_item
            SET unit = 'volume__mm3'
            WHERE unit = 'volume__um3'
        """)
    )


def upgrade() -> None:
    _migrate_data()
    op.sync_enum_values(
        enum_schema="public",
        enum_name="measurementunit",
        new_values=[
            "dimensionless",
            "linear_density__1_um",
            "area_density__1_um2",
            "volume_density__1_mm3",
            "linear__um",
            "area__um2",
            "volume__um3",
            "angle__radian",
        ],
        affected_columns=[
            TableReference(
                table_schema="public", table_name="measurement_item", column_name="unit"
            ),
            TableReference(
                table_schema="public", table_name="measurement_record", column_name="unit"
            ),
        ],
        enum_values_to_rename=[],
    )


def downgrade() -> None:
    op.sync_enum_values(
        enum_schema="public",
        enum_name="measurementunit",
        new_values=[
            "dimensionless",
            "linear_density__1_um",
            "area_density__1_um2",
            "volume_density__1_mm3",
            "linear__um",
            "area__um2",
            "volume__um3",
            "volume__mm3",
            "angle__radian",
        ],
        affected_columns=[
            TableReference(
                table_schema="public", table_name="measurement_item", column_name="unit"
            ),
            TableReference(
                table_schema="public", table_name="measurement_record", column_name="unit"
            ),
        ],
        enum_values_to_rename=[],
    )
    _revert_data()
