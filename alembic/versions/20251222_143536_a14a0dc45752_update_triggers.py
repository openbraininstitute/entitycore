"""Update triggers

Revision ID: a14a0dc45752
Revises: c313def86e58
Create Date: 2025-12-22 14:35:36.416801

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from alembic_utils.pg_trigger import PGTrigger
from sqlalchemy import text as sql_text

from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "a14a0dc45752"
down_revision: Union[str, None] = "c313def86e58"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    public_measurement_label_measurement_label_description_vector = PGTrigger(
        schema="public",
        signature="measurement_label_description_vector",
        on_entity="public.measurement_label",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON measurement_label\n            FOR EACH ROW EXECUTE FUNCTION\n                tsvector_update_trigger(description_vector, 'pg_catalog.english', description, name)",
    )
    op.create_entity(public_measurement_label_measurement_label_description_vector)

    # enforce running the new trigger on the existing records
    conn = op.get_bind()
    conn.execute(
        sql_text("""
            UPDATE measurement_label
            SET description = description
            WHERE description_vector IS NULL
        """)
    )


def downgrade() -> None:
    public_measurement_label_measurement_label_description_vector = PGTrigger(
        schema="public",
        signature="measurement_label_description_vector",
        on_entity="public.measurement_label",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON measurement_label\n            FOR EACH ROW EXECUTE FUNCTION\n                tsvector_update_trigger(description_vector, 'pg_catalog.english', description, name)",
    )
    op.drop_entity(public_measurement_label_measurement_label_description_vector)
