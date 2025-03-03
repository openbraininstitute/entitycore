"""empty message

Revision ID: f60009552cd3
Revises: 6f8d3b6426aa
Create Date: 2025-02-14 11:06:51.925448

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f60009552cd3"
down_revision: str | None = "6f8d3b6426aa"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint("uq_strain_id_species_id", "strain", ["id", "species_id"])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("uq_strain_id_species_id", "strain", type_="unique")
    # ### end Alembic commands ###
