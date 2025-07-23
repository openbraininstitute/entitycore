"""Add asset.storage_type column.

Revision ID: 69af7e08cc08
Revises: 992a74ce92fc
Create Date: 2025-07-23 11:01:19.819579

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "69af7e08cc08"
down_revision: Union[str, None] = "992a74ce92fc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    sa.Enum("aws_s3_internal", "aws_s3_open", name="storagetype").create(op.get_bind())
    op.add_column(
        "asset",
        sa.Column(
            "storage_type",
            postgresql.ENUM(
                "aws_s3_internal", "aws_s3_open", name="storagetype", create_type=False
            ),
            server_default="aws_s3_internal",
            nullable=False,
        ),
    )
    # remove server_default after the migration
    op.alter_column(
        "asset",
        "storage_type",
        server_default=None,
    )
    # ensure that path is unique per entity_id
    op.create_index(
        "uq_asset_entity_id_path",
        "asset",
        ["path", "entity_id"],
        unique=True,
        postgresql_where=sa.text("status != 'DELETED'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_asset_entity_id_path",
        table_name="asset",
        postgresql_where=sa.text("status != 'DELETED'"),
    )
    op.drop_column("asset", "storage_type")
    sa.Enum("aws_s3_internal", "aws_s3_open", name="storagetype").drop(op.get_bind())
