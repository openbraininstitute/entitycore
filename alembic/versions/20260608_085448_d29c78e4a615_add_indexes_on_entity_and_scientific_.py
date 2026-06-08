"""add indexes on entity and scientific_artifact and increase statistics on generation_type

Revision ID: d29c78e4a615
Revises: 619689419186
Create Date: 2026-06-08 08:54:48.710999

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "d29c78e4a615"
down_revision: Union[str, None] = "619689419186"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_entity_public_creation_date_id",
        "entity",
        ["creation_date", "id"],
        unique=False,
        postgresql_ops={"creation_date": "DESC"},
        postgresql_where=sa.text("authorized_public = true"),
    )
    op.create_index(
        "ix_scientific_artifact_brain_region_id_id",
        "scientific_artifact",
        ["brain_region_id", "id"],
        unique=False,
    )
    op.execute(
        "ALTER TABLE cell_morphology_protocol ALTER COLUMN generation_type SET STATISTICS 500"
    )
    op.execute("ANALYZE cell_morphology_protocol")


def downgrade() -> None:
    op.drop_index(
        "ix_scientific_artifact_brain_region_id_id",
        table_name="scientific_artifact",
    )
    op.drop_index(
        "ix_entity_public_creation_date_id",
        table_name="entity",
        postgresql_ops={"creation_date": "DESC"},
        postgresql_where=sa.text("authorized_public = true"),
    )
    op.execute(
        "ALTER TABLE cell_morphology_protocol ALTER COLUMN generation_type SET STATISTICS -1"
    )
