"""Add unique name per project trigger for analysis notebook template

Revision ID: 6d55006b013e
Revises: 8953d8ad7437
Create Date: 2026-08-21 12:59:28.977316

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from alembic_utils.pg_function import PGFunction
from alembic_utils.pg_trigger import PGTrigger
from sqlalchemy import text as sql_text

# revision identifiers, used by Alembic.
revision: str = "6d55006b013e"
down_revision: Union[str, None] = "8953d8ad7437"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop temporary migration table no longer needed
    op.drop_table("_person_sub_id_mapping")

    # Resolve duplicate names within the same project before enforcing uniqueness.
    # Appends _2, _3, etc. to duplicates ordered by creation date (oldest keeps original name).
    op.execute(sql_text("""
        WITH duplicates AS (
            SELECT
                ant.id,
                ant.name || '_' || ROW_NUMBER() OVER (
                    PARTITION BY e.authorized_project_id, ant.name
                    ORDER BY e.creation_date
                ) AS new_name,
                ROW_NUMBER() OVER (
                    PARTITION BY e.authorized_project_id, ant.name
                    ORDER BY e.creation_date
                ) AS rn
            FROM analysis_notebook_template ant
            JOIN entity e ON e.id = ant.id
        )
        UPDATE analysis_notebook_template ant
        SET name = d.new_name
        FROM duplicates d
        WHERE ant.id = d.id AND d.rn > 1
    """))

    public_unique_name_per_project = PGFunction(
        schema="public",
        signature="unique_name_per_project()",
        definition="""RETURNS TRIGGER AS $$
            DECLARE
                lock_key bigint;
                project_id uuid;
            BEGIN
                SELECT authorized_project_id INTO project_id
                FROM entity WHERE id = NEW.id;

                lock_key := (
                    ('x' || substring(md5(project_id::text || ':' || NEW.name), 1, 16))::bit(64)::bigint
                ) >> 1;
                PERFORM pg_advisory_xact_lock(lock_key);
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql""",
    )
    op.create_entity(public_unique_name_per_project)

    public_unique_name_trg_analysis_notebook_template = PGTrigger(
        schema="public",
        signature="unique_name_trg_analysis_notebook_template",
        on_entity="analysis_notebook_template",
        is_constraint=False,
        definition="""BEFORE INSERT OR UPDATE OF name ON analysis_notebook_template
            FOR EACH ROW EXECUTE FUNCTION unique_name_per_project()""",
    )
    op.create_entity(public_unique_name_trg_analysis_notebook_template)


def downgrade() -> None:
    public_unique_name_trg_analysis_notebook_template = PGTrigger(
        schema="public",
        signature="unique_name_trg_analysis_notebook_template",
        on_entity="analysis_notebook_template",
        is_constraint=False,
        definition="""BEFORE INSERT OR UPDATE OF name ON analysis_notebook_template
            FOR EACH ROW EXECUTE FUNCTION unique_name_per_project()""",
    )
    op.drop_entity(public_unique_name_trg_analysis_notebook_template)

    public_unique_name_per_project = PGFunction(
        schema="public",
        signature="unique_name_per_project()",
        definition="""RETURNS TRIGGER AS $$
            DECLARE
                lock_key bigint;
                project_id uuid;
            BEGIN
                SELECT authorized_project_id INTO project_id
                FROM entity WHERE id = NEW.id;

                lock_key := (
                    ('x' || substring(md5(project_id::text || ':' || NEW.name), 1, 16))::bit(64)::bigint
                ) >> 1;
                PERFORM pg_advisory_xact_lock(lock_key);
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql""",
    )
    op.drop_entity(public_unique_name_per_project)

    op.create_table(
        "_person_sub_id_mapping",
        sa.Column("person_id", sa.UUID(), autoincrement=False, nullable=True),
        sa.Column("sub_id", sa.UUID(), autoincrement=False, nullable=True),
    )
