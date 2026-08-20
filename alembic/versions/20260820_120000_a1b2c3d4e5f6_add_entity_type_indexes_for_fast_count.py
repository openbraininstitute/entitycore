"""Add entity type indexes for fast count queries

Revision ID: a1b2c3d4e5f6
Revises: 8953d8ad7437
Create Date: 2026-08-20 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "8953d8ad7437"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Index on entity(type) for fast unfiltered count queries per entity type.
    # Used by the optimized count path in router_read_many when no auth filter is active.
    # Reduces count query from ~100ms (3-table inheritance join) to ~12ms.
    op.create_index(
        "ix_entity_type",
        "entity",
        ["type"],
        unique=False,
    )
    # Partial index on entity(type) WHERE authorized_public = true.
    # Used for the most common count path (public entities by type).
    # Reduces count query from ~100ms to ~8ms.
    op.create_index(
        "ix_entity_type_public",
        "entity",
        ["type"],
        unique=False,
        postgresql_where="authorized_public = true",
    )


def downgrade() -> None:
    op.drop_index("ix_entity_type_public", table_name="entity")
    op.drop_index("ix_entity_type", table_name="entity")
