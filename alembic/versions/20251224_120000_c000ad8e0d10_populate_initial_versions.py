"""Populate initial versions

Revision ID: c000ad8e0d10
Revises: 060149884c38
Create Date: 2025-12-24 12:00:00.000000

"""

from collections.abc import Iterable
from functools import cache
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from alembic_postgresql_enum import TableReference

from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "c000ad8e0d10"
down_revision: Union[str, None] = "060149884c38"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OPERATION_TYPE = 0  # insert
EXCLUDED_TABLES = {
    "alembic_version",
    "transaction",
}


def _set_timeouts(conn: sa.Connection) -> None:
    conn.execute(sa.text("SET lock_timeout = '5s'"))
    conn.execute(sa.text("SET statement_timeout = '5min'"))


@cache
def _get_all_tables(conn: sa.Connection) -> list[str]:
    rows = conn.execute(
        sa.text(f"""
            SELECT schemaname, tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """),
    )
    return [row.tablename for row in rows]


def _get_versioned_tables(conn: sa.Connection) -> list[str]:
    all_tables = _get_all_tables(conn)
    return [t for t in all_tables if t.endswith("_version") and not t in EXCLUDED_TABLES]


def _get_original_tables(conn: sa.Connection) -> list[str]:
    versioned_tables = _get_versioned_tables(conn)
    return [t.removesuffix("_version") for t in versioned_tables]


def _lock_tables(conn: sa.Connection, tables: list[str]) -> None:
    conn.execute(
        sa.text(f"""
            LOCK TABLE {", ".join(tables)}
            IN ACCESS EXCLUSIVE MODE;
        """)
    )


def _insert_transaction_id(conn: sa.Connection) -> int:
    rows = conn.execute(
        sa.text(f"""
            INSERT INTO transaction (issued_at)
            VALUES (now())
            RETURNING id;
        """),
    )
    return rows.one()[0]


def _quoted(items: Iterable[str]) -> list[str]:
    """Return a list of strings enclosed with quotes, without any special escaping."""
    return [f'"{i}"' for i in items]


def _populate_tables(
    conn: sa.Connection,
    original_tables: list[str],
    versioned_tables: list[str],
    transaction_id: int,
) -> None:
    """Populate the versioned tables from the original tables."""
    insp = sa.inspect(conn)
    for original, versioned in zip(original_tables, versioned_tables, strict=True):
        cols = insp.get_columns(original, schema="public")
        fields = [c["name"] for c in cols]
        parameters = {"transaction_id": transaction_id, "operation_type": OPERATION_TYPE}
        conn.execute(
            sa.text(f"""
                INSERT INTO "{versioned}" ({",".join(_quoted(fields) + _quoted(parameters))})
                SELECT {",".join(_quoted(fields) + [f":{k}" for k in parameters])} FROM "{original}"
            """),
            parameters,
        )


def _verify_tables(
    conn: sa.Connection,
    original_tables: list[str],
    versioned_tables: list[str],
) -> None:
    errors = []
    for original, versioned in zip(original_tables, versioned_tables, strict=True):
        assert versioned == f"{original}_version"
        original_count = conn.execute(sa.text(f"SELECT COUNT(*) FROM {original};")).one()[0]
        versioned_count = conn.execute(sa.text(f"SELECT COUNT(*) FROM {versioned};")).one()[0]
        if original_count != versioned_count:
            errors.append(
                f"Table {original} has {original_count} original rows but "
                f"table {versioned} has {versioned_count} versioned rows."
            )
    if errors:
        msg = "\n".join(errors)
        raise RuntimeError(msg)


def _truncate_tables(conn: sa.Connection, tables: list[str]) -> None:
    conn.execute(sa.text(f"TRUNCATE {','.join(tables)} RESTART IDENTITY CASCADE"))


def upgrade() -> None:
    conn = op.get_bind()
    _set_timeouts(conn)
    all_tables = _get_all_tables(conn)
    original_tables = _get_original_tables(conn)
    versioned_tables = _get_versioned_tables(conn)
    for original, versioned in zip(original_tables, versioned_tables, strict=True):
        assert versioned == f"{original}_version", f"{original=}, {versioned=}"
    assert len(original_tables) == len(versioned_tables)
    _lock_tables(conn, tables=all_tables)
    transaction_id = _insert_transaction_id(conn)
    _populate_tables(
        conn,
        original_tables=original_tables,
        versioned_tables=versioned_tables,
        transaction_id=transaction_id,
    )
    _verify_tables(
        conn,
        original_tables=original_tables,
        versioned_tables=versioned_tables,
    )


def downgrade() -> None:
    conn = op.get_bind()
    _set_timeouts(conn)
    versioned_tables = _get_versioned_tables(conn)
    _truncate_tables(conn, tables=[*versioned_tables, "transaction"])
