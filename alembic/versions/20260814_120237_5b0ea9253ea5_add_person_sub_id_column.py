"""Add Person.sub_id column

Revision ID: 5b0ea9253ea5
Revises: 1695b8e6508c
Create Date: 2026-08-14 12:02:37.770855

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

import app.db.types

# revision identifiers, used by Alembic.
revision: str = "5b0ea9253ea5"
down_revision: Union[str, None] = "1695b8e6508c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("person", sa.Column("sub_id", sa.Uuid(), nullable=True))
    op.create_index(op.f("ix_person_sub_id"), "person", ["sub_id"], unique=True)
    op.create_foreign_key(
        op.f("fk_person_sub_id_platform_user"), "person", "platform_user", ["sub_id"], ["id"]
    )
    # Populate sub_id from the mapping table saved by the split_user_from_person migration
    connection = op.get_bind()
    has_mapping_table = connection.execute(
        sa.text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.tables"
            "  WHERE table_name = '_person_sub_id_mapping'"
            ")"
        )
    ).scalar()
    if has_mapping_table:
        op.execute("""
            UPDATE person p
            SET sub_id = m.sub_id
            FROM _person_sub_id_mapping m
            WHERE p.id = m.person_id
        """)


def downgrade() -> None:
    op.drop_constraint(op.f("fk_person_sub_id_platform_user"), "person", type_="foreignkey")
    op.drop_index(op.f("ix_person_sub_id"), table_name="person")
    op.drop_column("person", "sub_id")
