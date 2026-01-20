"""Add name and description to em_cell_mesh

Revision ID: a716c121f72b
Revises: 642ef45b49c6
Create Date: 2026-01-20 11:33:42.274086

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "a716c121f72b"
down_revision: Union[str, None] = "642ef45b49c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("em_cell_mesh", sa.Column("name", sa.String(), nullable=True))
    op.add_column("em_cell_mesh", sa.Column("description", sa.String(), nullable=True))
    op.add_column(
        "em_cell_mesh", sa.Column("description_vector", postgresql.TSVECTOR(), nullable=True)
    )
    op.execute(
        sa.text("""
        UPDATE em_cell_mesh
        SET description = '', name = concat(
            CASE
                WHEN em_dense_reconstruction_dataset.name ILIKE '%MICrONS%' THEN 'microns'
                WHEN em_dense_reconstruction_dataset.name ILIKE '%H01%' THEN 'h01'
                ELSE 'unknown'
            END,
            '_', em_cell_mesh.dense_reconstruction_cell_id
        )
        FROM em_dense_reconstruction_dataset
        WHERE em_dense_reconstruction_dataset.id = em_cell_mesh.em_dense_reconstruction_dataset_id
        """)
    )
    op.alter_column("em_cell_mesh", "name", nullable=False)
    op.alter_column("em_cell_mesh", "description", nullable=False)

    op.create_index(
        "ix_em_cell_mesh_description_vector",
        "em_cell_mesh",
        ["description_vector"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(op.f("ix_em_cell_mesh_name"), "em_cell_mesh", ["name"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_em_cell_mesh_name"), table_name="em_cell_mesh")
    op.drop_index(
        "ix_em_cell_mesh_description_vector", table_name="em_cell_mesh", postgresql_using="gin"
    )
    op.drop_column("em_cell_mesh", "description_vector")
    op.drop_column("em_cell_mesh", "description")
    op.drop_column("em_cell_mesh", "name")
