"""empty message

Revision ID: 878abb621e21
Revises: 1de0e9a0a8e1
Create Date: 2025-02-25 15:50:51.224784

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "878abb621e21"
down_revision: str | None = "48378d76d7b0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index(
        "ix_asset_fullpath",
        table_name="asset",
        postgresql_where="(status <> 'DELETED'::assetstatus)",
    )
    op.alter_column(
        "asset", "fullpath", existing_type=sa.VARCHAR(), nullable=True, new_column_name="full_path"
    )
    op.create_index(
        "ix_asset_full_path",
        "asset",
        ["full_path"],
        unique=True,
        postgresql_where=sa.text("status != 'DELETED'"),
    )
    op.add_column("asset", sa.Column("sha256_digest", sa.LargeBinary(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("asset", "sha256_digest")
    op.drop_index(
        "ix_asset_full_path", table_name="asset", postgresql_where=sa.text("status != 'DELETED'")
    )
    op.alter_column(
        "asset", "full_path", existing_type=sa.VARCHAR(), nullable=False, new_column_name="fullpath"
    )
    op.create_index(
        "ix_asset_fullpath",
        "asset",
        ["fullpath"],
        unique=True,
        postgresql_where="(status <> 'DELETED'::assetstatus)",
    )
