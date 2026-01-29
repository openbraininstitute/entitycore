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
TABLES_TO_DROP_STATUS = [
    {
        "table": "single_neuron_simulation",
        "column": "status",
        "enum": {
            "name": "singleneuronsimulationstatus",
            "values": ["started", "failure", "success"],
            "default": "success",
        },
    },
    {
        "table": "single_neuron_synaptome_simulation",
        "column": "status",
        "enum": {
            "name": "singleneuronsimulationstatus",
            "values": ["started", "failure", "success"],
            "default": "success",
        },
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


def _drop_table_statuses(op):
    for t in TABLES_TO_DROP_STATUS:
        op.drop_column(t["table"], t["column"])
    for t in TABLES_TO_DROP_STATUS:
        enum = postgresql.ENUM(*t["enum"]["values"], name=t["enum"]["name"])
        enum.drop(op.get_bind(), checkfirst=True)


def upgrade() -> None:
    activity_enum = _create_activity_status_column(op)
    _move_table_statuses(op)
    _drop_table_statuses(op)

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
        table_enum.create(conn, checkfirst=True)
        enums[t["enum"]["name"]] = table_enum
    for t in TABLES_TO_DROP_STATUS:
        table_enum = postgresql.ENUM(*t["enum"]["values"], name=t["enum"]["name"])
        table_enum.create(conn, checkfirst=True)
        enums[t["enum"]["name"]] = table_enum
    return enums


def _create_table_columns(enums):
    for t in TABLES_TO_MOVE_STATUS:
        op.add_column(
            t["table"],
            sa.Column(t["column"], enums[t["enum"]["name"]], nullable=True),
        )
    for t in TABLES_TO_DROP_STATUS:
        op.add_column(
            t["table"],
            sa.Column(
                t["column"],
                enums[t["enum"]["name"]],
                nullable=False,
                server_default=t["enum"]["default"],
            ),
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

    op.drop_column("activity", "status")
    _activity_enum().drop(conn)
