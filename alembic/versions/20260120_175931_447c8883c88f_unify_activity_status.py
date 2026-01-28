"""unify_activity_status

Revision ID: 447c8883c88f
Revises: 07064e01c345
Create Date: 2026-01-20 17:59:31.059678

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from sqlalchemy import Text, text, inspect
import app.db.types
from app.db.model import Activity

# revision identifiers, used by Alembic.
revision: str = "447c8883c88f"
down_revision: Union[str, None] = "07064e01c345"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLES_WITHOUT_STATUS = [
    "analysis_notebook_execution",
    "calibration",
    "circuit_extraction_config_generation",
    "ion_channel_modeling_config_generation",
    "simulation_generation",
    "skeletonization_config_generation",
    "validation",
]


# move status from these tables to the activity parent table
TABLES_TO_MOVE_STATUS = [
    {
        "table": "circuit_extraction_execution",
        "column": "status",
        "enum": {
            "name": "circuit_extraction_execution_status",
            "values": ["created", "pending", "running", "done", "error"],
        },
    },
    {
        "table": "skeletonization_execution",
        "column": "status",
        "enum": {
            "name": "skeletonizationexecutionstatus",
            "values": ["created", "pending", "running", "done", "error"],
        },
    },
    {
        "table": "ion_channel_modeling_execution",
        "column": "status",
        "enum": {
            "name": "ion_channel_modeling_execution_status",
            "values": ["created", "pending", "running", "done", "error"],
        },
    },
    {
        "table": "simulation_execution",
        "column": "status",
        "enum": {
            "name": "simulation_execution_status",
            "values": ["created", "pending", "running", "done", "error", "cancelled"],
        },
    },
]


# remap table status to activity status without moving it
TABLES_TO_REMAP_STATUS = [
    {
        "table": "single_neuron_simulation",
        "column": "status",
        "enum": {
            "name": "singleneuronsimulationstatus",
            "values": ["started", "failure", "success"],
        },
        "mapping": {"started": "created", "failure": "error", "success": "done"},
    },
    {
        "table": "single_neuron_synaptome_simulation",
        "column": "status",
        "enum": {
            "name": "singleneuronsimulationstatus",
            "values": ["started", "failure", "success"],
        },
        "mapping": {"started": "created", "failure": "error", "success": "done"},
    },
]


def _activity_enum():
    return sa.Enum(
        "created",
        "pending",
        "running",
        "done",
        "error",
        "cancelled",
        name="activitystatus",
    )


def _create_activity_status_column(op):
    """Create activity status collumn and fill it with done."""
    activity_enum = _activity_enum()
    activity_enum.create(op.get_bind())
    op.add_column(
        "activity",
        sa.Column("status", activity_enum, server_default=sa.text("'done'"), nullable=False),
    )
    return activity_enum


def _using_expr(col: str, mapping: dict[str, str]) -> str:
    if not mapping:
        return f"{col}::text::activitystatus"

    cases = "\n".join(f"WHEN '{old}' THEN '{new}'" for old, new in mapping.items())

    return f"""
    (
        CASE {col}::text
            {cases}
            ELSE {col}::text
        END
    )::activitystatus
    """


def _move_table_statuses(op):
    def _move_status(op, from_table: str, from_column: str, to_table: str, mapping):
        cases = _using_expr(f"{from_table}.{from_column}", mapping)
        op.execute(f"""
        UPDATE {to_table}
        SET status = {cases}
        FROM {from_table}
        WHERE {to_table}.id = {from_table}.id
        """)
        op.drop_column(from_table, "status")

    for t in TABLES_TO_MOVE_STATUS:
        _move_status(op, t["table"], t["column"], "activity", {})
        postgresql.ENUM(*t["enum"]["values"], name=t["enum"]["name"]).drop(op.get_bind())


def _remap_table_statuses(op, new_enum):
    enums_to_be_dropped = []
    for t in TABLES_TO_REMAP_STATUS:
        old_enum = postgresql.ENUM(*t["enum"]["values"], name=t["enum"]["name"])
        op.alter_column(
            t["table"],
            t["column"],
            existing_type=old_enum,
            type_=new_enum,
            existing_nullable=False,
            postgresql_using=_using_expr(t["column"], t["mapping"]),
        )
        enums_to_be_dropped.append(old_enum)
    for e in enums_to_be_dropped:
        e.drop(op.get_bind())


def upgrade() -> None:
    activity_enum = _create_activity_status_column(op)
    _move_table_statuses(op)
    _remap_table_statuses(op, activity_enum)

    conn = op.get_bind()

    # for the activity tables that did not have a status a "done" default
    # should be set in the acticity table
    for table in TABLES_WITHOUT_STATUS:
        count = conn.execute(
            text(f"""
            SELECT COUNT(*)
            FROM {table} t
            JOIN activity a ON a.id = t.id
            WHERE a.status != 'done'
        """)
        ).scalar()

        if count:
            raise RuntimeError(f"{table}: {count} rows have activity.status != 'done'")


def _create_table_enums(conn):
    """Create all old enums."""
    enums = {}
    for t in TABLES_TO_MOVE_STATUS:
        table_enum = postgresql.ENUM(*t["enum"]["values"], name=t["enum"]["name"])
        table_enum.create(conn)
        enums[t["enum"]["name"]] = table_enum
    for t in TABLES_TO_REMAP_STATUS:
        table_enum = postgresql.ENUM(*t["enum"]["values"], name=t["enum"]["name"])
        table_enum.create(conn)
        enums[t["enum"]["name"]] = table_enum
    return enums


def _create_table_columns(enums):
    for t in TABLES_TO_MOVE_STATUS:
        op.add_column(
            t["table"],
            sa.Column(t["column"], enums[t["enum"]["name"]], nullable=True),
        )


def _move_status_from_activity_to_tables(conn):
    for t in TABLES_TO_MOVE_STATUS:
        table_name = t["table"]
        enum_name = t["enum"]["name"]
        conn.execute(
            text(f"""
            UPDATE {table_name} t
            SET status = a.status::text::{enum_name}
            FROM activity a
            WHERE a.id = t.id
        """)
        )


def _invert_remap_table_statuses(conn, old_enum, enums):
    enums_to_be_dropped = []
    for t in TABLES_TO_REMAP_STATUS:
        table_name = t["table"]
        table_column = t["column"]
        new_enum_name = t["enum"]["name"]
        inverse_mapping = {v: k for k, v in t["mapping"].items()}

        str_using = _using_expr(table_column, inverse_mapping).replace(
            "activitystatus", new_enum_name
        )

        conn.execute(
            text(f"""
        ALTER TABLE {table_name}
        ALTER COLUMN {table_column} TYPE {new_enum_name}
        USING {str_using}
        """)
        )


def downgrade() -> None:
    conn = op.get_bind()

    enums = _create_table_enums(conn)

    # create nullable status columns for tables
    _create_table_columns(enums)

    # copy values from activity to tables
    _move_status_from_activity_to_tables(conn)

    # remove nullability
    for t in TABLES_TO_MOVE_STATUS:
        op.alter_column(
            t["table"],
            t["column"],
            existing_type=enums[t["enum"]["name"]],
            nullable=False,
        )

    # invert statuses back to local ones
    activity_enum = _activity_enum()
    _invert_remap_table_statuses(conn, activity_enum, enums)

    op.drop_column("activity", "status")
    activity_enum.drop(conn)
