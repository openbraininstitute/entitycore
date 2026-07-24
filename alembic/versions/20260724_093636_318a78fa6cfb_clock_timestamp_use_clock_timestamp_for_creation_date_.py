"""Use clock_timestamp for creation_date and update_date

Revision ID: 318a78fa6cfb
Revises: 79dbeada57f3
Create Date: 2026-07-24 09:36:36.170953

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "318a78fa6cfb"
down_revision: Union[str, None] = "79dbeada57f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = [
    "activity",
    "agent",
    "annotation",
    "annotation_body",
    "asset",
    "brain_region",
    "brain_region_hierarchy",
    "contribution",
    "derivation",
    "entity",
    "etype_class",
    "etype_classification",
    "external_url",
    "ion",
    "ion_channel",
    "license",
    "measurement_annotation",
    "measurement_label",
    "mtype_class",
    "mtype_classification",
    "publication",
    "role",
    "scientific_artifact_external_url_link",
    "scientific_artifact_publication_link",
    "species",
    "strain",
]


def upgrade() -> None:
    for table in _TABLES:
        op.alter_column(table, "creation_date", server_default=sa.text("clock_timestamp()"))
        op.alter_column(table, "update_date", server_default=sa.text("clock_timestamp()"))


def downgrade() -> None:
    for table in _TABLES:
        op.alter_column(table, "creation_date", server_default=sa.text("now()"))
        op.alter_column(table, "update_date", server_default=sa.text("now()"))
