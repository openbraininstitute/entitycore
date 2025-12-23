import logging
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import Any

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import Table
from sqlalchemy.orm import Mapper

from app.db.model import Activity, Base, Entity

L = logging.getLogger()

TABLES: dict[str, Mapper] = {
    mapper.class_.__tablename__: mapper
    for mapper in Base.registry.mappers
    if getattr(mapper.class_, "__tablename__", None)
}
BUILD_SCRIPT = "build_database_archive.sh"
LOAD_SCRIPT = "load.sh"

SCRIPT_VERSION = 1
SETUP_PG_PARAMS = """
export PGUSER="${PGUSER:-entitycore}"
export PGHOST="${PGHOST:-127.0.0.1}"
export PGPORT="${PGPORT:-5432}"
export PGDATABASE="${PGDATABASE:-entitycore}"
if [[ -z "${PGPASSWORD:-}" ]]; then
    read -r -s -p "Enter password for postgresql://$PGUSER@$PGHOST:$PGPORT/$PGDATABASE: " PGPASSWORD
    echo
    export PGPASSWORD
fi
"""
SETUP_PSQL = """
PSQL_BIN="${PSQL_BIN:-psql}"
PSQL_PARAMS="${PSQL_PARAMS:--q --echo-errors --set=ON_ERROR_STOP=on}"
PSQL="${PSQL_BIN} ${PSQL_PARAMS}"
if ! command -v "$PSQL_BIN" &>/dev/null; then
    echo "Error: psql not found, please set the correct PSQL_BIN variable."
    exit 1
fi
"""
SETUP_PG_DUMP = """
PG_DUMP_BIN="${PG_DUMP_BIN:-pg_dump}"
PG_DUMP_PARAMS="${PG_DUMP_PARAMS:---no-owner --no-privileges}"
PG_DUMP="${PG_DUMP_BIN} ${PG_DUMP_PARAMS}"
if ! command -v "$PG_DUMP_BIN" &>/dev/null; then
    echo "Error: pg_dump not found, please set the correct PG_DUMP_BIN variable."
    exit 1
fi
"""
SETUP_MAKESELF = """
MAKESELF_BIN="${MAKESELF_BIN:-makeself}"
if ! command -v "$MAKESELF_BIN" &>/dev/null; then
    echo "Error: makeself not found, please set the correct MAKESELF_BIN variable."
    exit 1
fi
MAKESELF_PARAMS="${MAKESELF_PARAMS:-}"
MAKESELF="${MAKESELF_BIN} ${MAKESELF_PARAMS}"
"""


@dataclass(kw_only=True)
class JoinInfo:
    """Information needed to build a join query between `main_table` and `joined_table`."""

    joined_table: str
    joined_table_col: str
    main_table_col: str
    nullable: bool


def get_current_db_version() -> str:
    """Return the current db version from the migration files.

    Assuming that the migration files are in sync with the db model,
    the list of exported tables is consistent with that revision only.
    """
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    if not (head := script.get_current_head()):
        msg = "Head revision not found"
        raise RuntimeError(msg)
    L.info("Alembic head revision: %s", head)
    return head


def _find_linked_authenticated_resources(table: Table) -> list[JoinInfo]:
    """Iterate over the foreign keys and return the list of JoinInfo."""
    linked: list[JoinInfo] = []
    for column in table.columns:
        assert column.nullable is not None  # noqa: S101
        for fk in column.foreign_keys:
            other = TABLES[fk.column.table.name].class_
            if issubclass(other, Entity):
                linked.append(
                    JoinInfo(
                        joined_table="entity",
                        joined_table_col=fk.column.name,
                        main_table_col=column.name,
                        nullable=column.nullable,
                    )
                )
            elif issubclass(other, Activity):
                linked.append(
                    JoinInfo(
                        joined_table="activity",
                        joined_table_col=fk.column.name,
                        main_table_col=column.name,
                        nullable=column.nullable,
                    )
                )
    return linked


def _export_with_joins(tablename: str, joins: list[JoinInfo], *, authorized: bool = False) -> str:
    """Build and return the export query for tables with foreign keys.

    Limitations:
        - Only direct (one-level) relationships from the main table are supported.
        - The joined column in the foreign tables is always assumed to be `id`.

    Args:
        tablename: Name of the main table.
        joins: A list of JoinInfo defining the tables to join and the foreign key field.
        authorized: If True, include the condition `authorized_public IS true`
            on the main table as well as all joined tables.
    """
    join_clauses = " ".join(
        f"{'LEFT JOIN' if join.nullable else 'JOIN'} {join.joined_table} AS t{i} "
        f"ON t{i}.{join.joined_table_col}=t0.{join.main_table_col}"
        for i, join in enumerate(joins, start=1)
    )
    where_clauses = " AND ".join(
        (["t0.authorized_public IS true"] if authorized else [])
        + [
            # not false = true or null (for left joins)
            f"t{i}.authorized_public IS NOT false"
            for i, _ in enumerate(joins, start=1)
        ]
    )
    return f"""
        SELECT t0.* FROM {tablename} AS t0
        {join_clauses}
        WHERE {where_clauses or "TRUE"}
        """  # noqa: S608


def get_automatic_queries() -> dict[str, str]:
    queries = {}
    for tablename, table in sorted(Base.metadata.tables.items()):
        authorized = "authorized_public" in table.columns
        linked = _find_linked_authenticated_resources(table)
        L.debug("Table %s: linked=%s, authorized=%s", table.name, linked, authorized)
        queries[tablename] = _export_with_joins(tablename, linked, authorized=authorized)
    return queries


def get_manual_queries() -> dict[str, str]:
    """Return the mapping used to generate the manual queries for each table."""
    return {
        "alembic_version": """SELECT * FROM alembic_version""",
        "measurement_item": """
            SELECT t0.* FROM measurement_item AS t0
            JOIN measurement_kind AS mk ON mk.id=t0.measurement_kind_id
            JOIN measurement_annotation AS ma ON ma.id=mk.measurement_annotation_id
            JOIN entity AS e ON e.id=ma.entity_id
            WHERE e.authorized_public IS true
            """,
        "measurement_kind": """
            SELECT t0.* FROM measurement_kind AS t0
            JOIN measurement_annotation AS ma ON ma.id=t0.measurement_annotation_id
            JOIN entity AS e ON e.id=ma.entity_id
            WHERE e.authorized_public IS true
            """,
    }


def get_formatted_queries() -> dict[str, str]:
    """Return the formatted queries."""
    manual_queries = get_manual_queries()
    automatic_queries = get_automatic_queries()
    queries = automatic_queries | manual_queries
    return {table: dedent(q).strip().replace("\n", " ") for table, q in queries.items()}


def format_content(content: str, params: dict[str, Any]) -> str:
    """Format the content after dedenting it."""
    content = dedent(content)
    content = content.format(**params).lstrip()
    return content


def write_script(filepath: Path, content: str) -> None:
    """Write the content to file and make it executable."""
    L.info("Writing %s", filepath)
    filepath.write_text(content, encoding="utf-8")
    filepath.chmod(mode=0o755)  # make the file executable


def _get_load_script_content(db_version: str) -> str:
    """Return the content of the load script."""
    content = r"""
        #!/bin/bash
        # Automatically generated, do not edit!
        set -euo pipefail
        SCRIPT_VERSION="{script_version}"
        SCRIPT_DB_VERSION="{db_version}"
        echo "DB load (version $SCRIPT_VERSION for db version $SCRIPT_DB_VERSION)"

        {setup_psql}
        {setup_pg_params}

        DATA_DIR="data"
        SCHEMA_PRE_DATA="$DATA_DIR/schema_pre_data.sql"
        SCHEMA_POST_DATA="$DATA_DIR/schema_post_data.sql"

        if [[
            ! -f "${{SCHEMA_PRE_DATA:-}}" ||
            ! -f "${{SCHEMA_POST_DATA:-}}" ||
            ! -d "${{DATA_DIR:-}}"
        ]]; then
            echo "Data to load not found."
            exit 1
        fi

        echo "WARNING! All the data in the database $PGDATABASE at $PGHOST:$PGPORT will be deleted!"
        read -r -p "Press Enter to continue or Ctrl+C to cancel..."

        echo "Dropping and recreating database..."
        dropdb --if-exists --force "$PGDATABASE"
        createdb "$PGDATABASE"

        echo "Restoring schema_pre_data to destination DB..."
        $PSQL -f "$SCHEMA_PRE_DATA"

        echo "Importing data..."
        $PSQL <<EOF
        BEGIN;
        $(for FILE in "$DATA_DIR"/*.csv; do
            TABLE=$(basename "$FILE" .csv)
            printf '\\echo Restoring table %s\n' "$TABLE"
            printf '\\copy %s FROM '%s' WITH CSV HEADER;\n' "$TABLE" "$FILE"
        done)
        COMMIT;
        EOF

        echo "Restoring schema_post_data to destination DB..."
        $PSQL -f "$SCHEMA_POST_DATA"

        echo "Running ANALYZE..."
        $PSQL -c "ANALYZE;"

        echo "All done."
    """
    return format_content(
        content,
        params={
            "script_version": SCRIPT_VERSION,
            "setup_pg_params": SETUP_PG_PARAMS,
            "setup_psql": SETUP_PSQL,
            "db_version": db_version,
        },
    )


def _get_build_script_content(queries: dict[str, str], db_version: str) -> str:
    """Return the content of the build script.

    In detail:

    - Dump the database schema and data to files, one per table.
    - Create an archive containing the dumped files and the load script
      (the dump script is included only for inspection).
    - Create a self-extracting archive.
    """
    content = r"""
        #!/bin/bash
        # Automatically generated, do not edit!
        set -euo pipefail
        SCRIPT_VERSION="{script_version}"
        SCRIPT_DB_VERSION="{db_version}"
        echo "DB dump (version $SCRIPT_VERSION for db version $SCRIPT_DB_VERSION)"

        {setup_makeself}
        {setup_psql}
        {setup_pg_dump}
        {setup_pg_params}

        WORK_DIR=$(mktemp -d)
        cleanup() {{
            printf '\nCleaning up %s\n' "$WORK_DIR"
            rm -rf "$WORK_DIR"
        }}
        trap cleanup EXIT

        DATA_DIR="$WORK_DIR/data"
        SCHEMA_PRE_DATA="$DATA_DIR/schema_pre_data.sql"
        SCHEMA_POST_DATA="$DATA_DIR/schema_post_data.sql"

        ACTUAL_DB_VERSION=$($PSQL -t -A -c "SELECT version_num FROM alembic_version")
        if [[ "$ACTUAL_DB_VERSION" != "$SCRIPT_DB_VERSION" ]]; then
            echo "Actual db version ($ACTUAL_DB_VERSION) != script version ($SCRIPT_DB_VERSION)"
            exit 1
        fi

        INSTALL_SCRIPT="install_db_$(date +%Y%m%d)_$SCRIPT_DB_VERSION.run"

        echo "Dump database $PGDATABASE from $PGHOST:$PGPORT"

        mkdir -p "$DATA_DIR"

        echo "Dumping schema..."
        $PG_DUMP --schema-only --format=p --section=pre-data > "$SCHEMA_PRE_DATA"
        $PG_DUMP --schema-only --format=p --section=post-data > "$SCHEMA_POST_DATA"

        echo "Dumping data..."
        $PSQL <<EOF
        BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ;
        SET TRANSACTION READ ONLY;
        {psql_commands}
        COMMIT;
        EOF

        echo -e "\nBuilding install script..."

        install -m 755 /dev/stdin "$WORK_DIR/{load_script}" <<'EOF_LOAD_SCRIPT'
        {load_script_content}
        EOF_LOAD_SCRIPT

        cp "$0" "$WORK_DIR" # for inspection
        LABEL="DB installer (version $SCRIPT_VERSION for db version $SCRIPT_DB_VERSION)"
        $MAKESELF "$WORK_DIR" "$INSTALL_SCRIPT" "$LABEL" "./{load_script}"

        echo "All done."
    """
    psql_commands = "\n".join(
        f"\\echo Dumping table {name}\n\\copy ({query}) TO '$DATA_DIR/{name}.csv' WITH CSV HEADER;"
        for name, query in queries.items()
    )
    load_script_content = _get_load_script_content(db_version=db_version)
    return format_content(
        content,
        params={
            "script_version": SCRIPT_VERSION,
            "setup_psql": SETUP_PSQL,
            "setup_pg_dump": SETUP_PG_DUMP,
            "setup_pg_params": SETUP_PG_PARAMS,
            "setup_makeself": SETUP_MAKESELF,
            "load_script": LOAD_SCRIPT,
            "load_script_content": load_script_content,
            "psql_commands": psql_commands,
            "db_version": db_version,
        },
    )


def main():
    """Main entry point."""
    L.info("Updating scripts...")
    db_version = get_current_db_version()
    queries = get_formatted_queries()
    scripts_dir = Path(__file__).parent
    write_script(
        scripts_dir / BUILD_SCRIPT,
        content=_get_build_script_content(queries=queries, db_version=db_version),
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    main()
