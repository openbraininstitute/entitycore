"""Default migration message

Revision ID: e84f2d85a325
Revises: 9ec554465df5
Create Date: 2025-06-13 11:30:44.791182

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "e84f2d85a325"
down_revision: Union[str, None] = "9ec554465df5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("activity", sa.Column("authorized_project_id", sa.Uuid(), nullable=False))
    op.add_column("activity", sa.Column("authorized_public", sa.Boolean(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("activity", "authorized_public")
    op.drop_column("activity", "authorized_project_id")
    # ### end Alembic commands ###
