"""add indexes on generation and usage tables

Revision ID: 619689419186
Revises: 0c555bea9437
Create Date: 2026-06-06 13:49:31.835553

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "619689419186"
down_revision: Union[str, None] = "0c555bea9437"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.create_index(
            "ix_generation_activity_entity",
            "generation",
            ["generation_activity_id", "generation_entity_id"],
            unique=False,
            postgresql_concurrently=True,
        )
        op.create_index(
            "ix_usage_activity_entity",
            "usage",
            ["usage_activity_id", "usage_entity_id"],
            unique=False,
            postgresql_concurrently=True,
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.drop_index("ix_usage_activity_entity", table_name="usage", postgresql_concurrently=True)
        op.drop_index(
            "ix_generation_activity_entity", table_name="generation", postgresql_concurrently=True
        )
