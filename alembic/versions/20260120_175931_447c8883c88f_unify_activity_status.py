"""unify_activity_status

Revision ID: 447c8883c88f
Revises: 07064e01c345
Create Date: 2026-01-20 17:59:31.059678

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from sqlalchemy import Text, text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "447c8883c88f"
down_revision: Union[str, None] = "07064e01c345"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


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
        "table": "memodel",
        "column": "validation_status",
        "enum": {
            "name": "me_model_validation_status",
            "values": ["created", "initialized", "running", "done", "error"],
        },
        "mapping": {"initialized": "pending"},
    },
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


def _create_activity_status_column(op):
    """Create activity status collumn and fill it with done."""
    activity_enum = sa.Enum(
        "created",
        "pending",
        "running",
        "done",
        "error",
        "cancelled",
        name="activitystatus",
    )
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
    rows = conn.execute(
        text("""
        SELECT c.relname
        FROM pg_inherits i
        JOIN pg_class p ON i.inhparent = p.oid
        JOIN pg_class c ON i.inhrelid = c.oid
        JOIN pg_attribute a ON a.attrelid = c.oid
        WHERE p.relname = 'activity'
          AND a.attname = 'status'
          AND a.attisdropped = false
    """)
    ).fetchall()

    if rows:
        tables = ", ".join(r[0] for r in rows)
        raise RuntimeError(
            f"Migration invariant violated: "
            f"child tables of activity still define 'status': {tables}"
        )


def downgrade() -> None:
    raise RuntimeError("The migration cannot be safely downgraded.")
