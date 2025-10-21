import logging  # noqa: INP001
from pathlib import Path
from textwrap import dedent
from typing import Any

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy.orm import Mapper

from app.db.model import Base

L = logging.getLogger()

TABLES: dict[str, Mapper] = {
    mapper.class_.__tablename__: mapper
    for mapper in Base.registry.mappers
    if mapper.class_.__tablename__
}
BUILD_SCRIPT = "build_database_archive.sh"
LOAD_SCRIPT = "_load.sh"
BOOTSTRAP_SCRIPT = "_bootstrap.sh"

SCRIPT_VERSION = 1
SETUP_PSQL = """
export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"
export PATH=/usr/pgsql-17/bin:$PATH

export PGUSER="${PGUSER:-entitycore}"
export PGHOST="${PGHOST:-127.0.0.1}"
export PGPORT="${PGPORT:-5432}"
export PGDATABASE="${PGDATABASE:-entitycore}"

PSQL_BIN="${PSQL_BIN:-psql}"
PSQL_PARAMS="${PSQL_PARAMS:--q --echo-errors --set=ON_ERROR_STOP=on}"
PSQL="${PSQL_BIN} ${PSQL_PARAMS}"

if ! command -v "$PSQL_BIN" &>/dev/null; then
    echo "Error: psql not found in PATH, please set the correct PATH or the PSQL_BIN variable."
    exit 1
fi

if [[ -z "${PGPASSWORD:-}" ]]; then
    read -r -s -p "Enter password for postgresql://$PGUSER@$PGHOST:$PGPORT/$PGDATABASE: " PGPASSWORD
    echo
    export PGPASSWORD
fi
"""
SETUP_WORK_DIR = """
WORK_DIR=$(mktemp -d -t dump)
cleanup() {
    printf '\\nCleaning up %s\\n' "$WORK_DIR"
    rm -rf "$WORK_DIR"
}
trap cleanup EXIT
export WORK_DIR
export DATA_DIR="$WORK_DIR/data"
export SCHEMA_PRE_DATA="$DATA_DIR/schema_pre_data.sql"
export SCHEMA_POST_DATA="$DATA_DIR/schema_post_data.sql"
"""


def get_current_head() -> str:
    """Return the current head revision from the migration files.

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


def get_queries() -> dict[str, str]:
    """Return the mapping used to generate the export queries for each table."""
    callables = {
        # alembic
        "alembic_version": lambda t: _export_all(t, skip_check=True),
        # global tables without authorized_public
        "agent": _export_all,
        "brain_region": _export_all,
        "brain_region_hierarchy": _export_all,
        "annotation_body": _export_all,
        "consortium": _export_all,
        "datamaturity_annotation_body": _export_all,
        "etype_class": _export_all,
        "external_url": _export_all,
        "ion": _export_all,
        "ion_channel": _export_all,
        "license": _export_all,
        "mtype_class": _export_all,
        "organization": _export_all,
        "person": _export_all,
        "publication": _export_all,
        "role": _export_all,
        "species": _export_all,
        "strain": _export_all,
        # base tables with authorized_public
        "entity": _export_public,
        "activity": _export_public,
        # children of entity
        "analysis_notebook_environment": lambda t: _export_child(t, "entity"),
        "analysis_notebook_result": lambda t: _export_child(t, "entity"),
        "analysis_notebook_template": lambda t: _export_child(t, "entity"),
        "analysis_software_source_code": lambda t: _export_child(t, "entity"),
        "brain_atlas": lambda t: _export_child(t, "entity"),
        "brain_atlas_region": lambda t: _export_child(t, "entity"),
        "cell_composition": lambda t: _export_child(t, "entity"),
        "cell_morphology": lambda t: _export_child(t, "entity"),
        "cell_morphology_protocol": lambda t: _export_child(t, "entity"),
        "circuit": lambda t: _export_child(t, "entity"),
        "electrical_cell_recording": lambda t: _export_child(t, "entity"),
        "electrical_recording": lambda t: _export_child(t, "entity"),
        "electrical_recording_stimulus": lambda t: _export_child(t, "entity"),
        "em_cell_mesh": lambda t: _export_child(t, "entity"),
        "em_dense_reconstruction_dataset": lambda t: _export_child(t, "entity"),
        "emodel": lambda t: _export_child(t, "entity"),
        "scientific_artifact": lambda t: _export_child(t, "entity"),
        "experimental_bouton_density": lambda t: _export_child(t, "entity"),
        "experimental_neuron_density": lambda t: _export_child(t, "entity"),
        "experimental_synapses_per_connection": lambda t: _export_child(t, "entity"),
        "ion_channel_model": lambda t: _export_child(t, "entity"),
        "ion_channel_recording": lambda t: _export_child(t, "entity"),
        "me_type_density": lambda t: _export_child(t, "entity"),
        "memodel": lambda t: _export_child(t, "entity"),
        "simulation": lambda t: _export_child(t, "entity"),
        "simulation_campaign": lambda t: _export_child(t, "entity"),
        "simulation_result": lambda t: _export_child(t, "entity"),
        "single_neuron_simulation": lambda t: _export_child(t, "entity"),
        "single_neuron_synaptome": lambda t: _export_child(t, "entity"),
        "single_neuron_synaptome_simulation": lambda t: _export_child(t, "entity"),
        "subject": lambda t: _export_child(t, "entity"),
        # children of activity
        "analysis_notebook_execution": lambda t: _export_child(t, "activity"),
        "calibration": lambda t: _export_child(t, "activity"),
        "simulation_execution": lambda t: _export_child(t, "activity"),
        "simulation_generation": lambda t: _export_child(t, "activity"),
        "validation": lambda t: _export_child(t, "activity"),
        # other tables and association tables
        "annotation": lambda t: _export_single_join(t, "entity", "entity_id"),
        "asset": lambda t: _export_single_join(t, "entity", "entity_id"),
        "contribution": lambda t: _export_single_join(t, "entity", "entity_id"),
        "derivation": lambda t: _export_double_join(
            t, ("entity", "used_id"), ("entity", "generated_id")
        ),
        "etype_classification": lambda t: f"""
            SELECT {t}.* FROM {t}
            JOIN entity AS e ON e.id={t}.entity_id
            WHERE {t}.authorized_public IS true
            AND e.authorized_public IS true
            """,  # noqa: S608
        "generation": lambda t: _export_double_join(
            t, ("entity", "generation_entity_id"), ("activity", "generation_activity_id")
        ),
        "ion_channel_model__emodel": lambda t: _export_double_join(
            t, ("entity", "ion_channel_model_id"), ("entity", "emodel_id")
        ),
        "measurement_annotation": lambda t: _export_single_join(t, "entity", "entity_id"),
        "measurement_item": lambda t: f"""
            SELECT {t}.* FROM {t}
            JOIN measurement_kind AS mk ON mk.id={t}.measurement_kind_id
            JOIN measurement_annotation AS ma ON ma.id=mk.measurement_annotation_id
            JOIN entity AS e ON e.id=ma.entity_id
            WHERE e.authorized_public IS true
            """,  # noqa: S608
        "measurement_kind": lambda t: f"""
            SELECT {t}.* FROM {t}
            JOIN measurement_annotation AS ma ON ma.id={t}.measurement_annotation_id
            JOIN entity AS e ON e.id=ma.entity_id
            WHERE e.authorized_public IS true
            """,  # noqa: S608
        "measurement_record": lambda t: _export_single_join(t, "entity", "entity_id"),
        "memodel_calibration_result": lambda t: f"""
            SELECT {t}.* FROM {t}
            JOIN entity AS e1 ON e1.id={t}.id
            JOIN entity AS e2 ON e2.id={t}.calibrated_entity_id
            WHERE e1.authorized_public IS true
            AND e2.authorized_public IS true
            """,  # noqa: S608
        "mtype_classification": lambda t: f"""
            SELECT {t}.* FROM {t}
            JOIN entity AS e ON e.id={t}.entity_id
            WHERE {t}.authorized_public IS true
            AND e.authorized_public IS true
            """,  # noqa: S608
        "scientific_artifact_external_url_link": lambda t: _export_single_join(
            t, "entity", "scientific_artifact_id"
        ),
        "scientific_artifact_publication_link": lambda t: _export_single_join(
            t, "entity", "scientific_artifact_id"
        ),
        "usage": lambda t: _export_double_join(
            t, ("entity", "usage_entity_id"), ("activity", "usage_activity_id")
        ),
        "validation_result": lambda t: f"""
            SELECT {t}.* FROM {t}
            JOIN entity AS e1 ON e1.id={t}.id
            JOIN entity AS e2 ON e2.id={t}.validated_entity_id
            WHERE e1.authorized_public IS true
            AND e2.authorized_public IS true
            """,  # noqa: S608
    }
    return {
        table: dedent(func(table)).strip().replace("\n", " ") for table, func in callables.items()
    }


def _ensure_table(tablename: str) -> Mapper:
    """Ensure that a table is defined in the base mapper."""
    if not (table := TABLES.get(tablename)):
        msg = f"Table {tablename} doesn't exist"
        raise ValueError(msg)
    return table


def _ensure_column(tablename: str, column: str, *, exist: bool) -> None:
    """Ensure that a column exists (or not) in the given table."""
    table = _ensure_table(tablename)
    if exist and column not in table.columns:
        msg = f"Column {tablename}.{column} expected but not found"
        raise ValueError(msg)
    if not exist and column in table.columns:
        msg = f"Column {tablename}.{column} not expected but found"
        raise ValueError(msg)


def _export_all(tablename: str, *, skip_check: bool = False) -> str:
    """Build and return the export query for global tables without authorized_public.

    Args:
        tablename: table name.
        skip_check: True to skip the validation.
    """
    if not skip_check:
        _ensure_column(tablename, "authorized_public", exist=False)
    return f"""SELECT {tablename}.* FROM {tablename}"""  # noqa: S608


def _export_public(tablename: str) -> str:
    """Build and return the export query for base tables with authorized_public.

    Args:
        tablename: table name.
    """
    _ensure_column(tablename, "authorized_public", exist=True)
    return f"""SELECT {tablename}.* from {tablename} WHERE authorized_public IS true"""  # noqa: S608


def _export_child(tablename: str, parent: str) -> str:
    """Build and return the export query for children tables.

    Args:
        tablename: main table name.
        parent: parent table to join.
    """
    _ensure_column(tablename, "authorized_public", exist=True)
    return f"""
        SELECT {tablename}.* from {tablename}
        JOIN {parent} USING (id)
        WHERE {parent}.authorized_public IS true
        """  # noqa: S608


def _export_single_join(tablename: str, join: str, join_on: str) -> str:
    """Build and return the export query for linked tables (one to many).

    Args:
        tablename: main table name.
        join: table to join.
        join_on: the field in the main table to be used for the join.
    """
    assert "authorized_public" not in TABLES[tablename].columns  # noqa: S101
    return f"""
        SELECT {tablename}.* FROM {tablename}
        JOIN {join} AS t ON t.id={tablename}.{join_on}
        WHERE t.authorized_public IS true
        """  # noqa: S608


def _export_double_join(tablename: str, join_1: tuple[str, str], join_2: tuple[str, str]) -> str:
    """Build and return the export query for association tables (many to many).

    Args:
        tablename: main table name.
        join_1: tuple (join, join_on), where join is the first table to join,
            and join_on is the field in the main table to be used for the join.
        join_2: tuple (join, join_on), where join is the second table to join,
            and join_on is the field in the main table to be used for the join.
    """
    assert "authorized_public" not in TABLES[tablename].columns  # noqa: S101
    return f"""
        SELECT {tablename}.* FROM {tablename}
        JOIN {join_1[0]} AS t1 ON t1.id={tablename}.{join_1[1]}
        JOIN {join_2[0]} AS t2 ON t2.id={tablename}.{join_2[1]}
        WHERE t1.authorized_public IS true
        AND t2.authorized_public IS true
        """  # noqa: S608


def check_queries(queries: dict[str, str]) -> None:
    """Verify the consistency of the export queries."""
    queries_set = set(queries)
    all_tables = set(Base.metadata.tables) | {"alembic_version"}
    if diff := all_tables - queries_set:
        L.warning("Missing tables in the configuration: %s", sorted(diff))
    if diff := queries_set - all_tables:
        L.warning("Extra tables in the configuration: %s", sorted(diff))


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


def _get_bootstrap_script_content() -> str:
    """Return the content of the bootstrap script."""
    content = r"""
        #!/bin/bash
        # Automatically generated, do not edit!
        set -euo pipefail
        {setup_work_dir}

        ARCHIVE_LINE=$(awk '/^__ARCHIVE_BELOW__/ {{ print NR + 1; exit 0; }}' "$0")
        tail -n +$ARCHIVE_LINE "$0" | tar -xzv -C "$WORK_DIR"
        cd "$WORK_DIR"
        ./{load_script}
        exit 0
        __ARCHIVE_BELOW__
    """
    return format_content(
        content,
        params={
            "setup_work_dir": SETUP_WORK_DIR,
            "load_script": LOAD_SCRIPT,
        },
    )


def _get_load_script_content() -> str:
    """Return the content of the load script."""
    content = r"""
        #!/bin/bash
        # Automatically generated, do not edit!
        set -euo pipefail
        {setup_psql}

        echo "DB LOAD (version {script_version})"
        echo "Restore database $PGDATABASE to $PGHOST:$PGPORT"

        if [[
            ! -f "${{SCHEMA_PRE_DATA:-}}" ||
            ! -f "${{SCHEMA_POST_DATA:-}}" ||
            ! -d "${{DATA_DIR:-}}"
        ]]; then
            echo "Data to load not found."
            exit 1
        fi

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
            "setup_psql": SETUP_PSQL,
        },
    )


def _get_build_script_content(queries: dict[str, str], head: str) -> str:
    """Return the content of the build script.

    In detail:

    - Dump the database schema and data to files, one per table.
    - Create an archive containing the dumped files and the load script
      (the dump and bootstrap scripts are included only for reference).
    - Create an install script by concatenating the bootstrap script with the archive.
    """
    content = r"""
        #!/bin/bash
        # Automatically generated, do not edit!
        set -euo pipefail
        {setup_psql}
        {setup_work_dir}

        echo "DB DUMP (version {script_version} for db version {head})"

        EXPECTED_DB_VERSION="{head}"
        DB_VERSION=$($PSQL -t -A -c "SELECT version_num FROM alembic_version")
        if [[ "$DB_VERSION" != "$EXPECTED_DB_VERSION" ]]; then
            echo "Database version ($DB_VERSION) != expected ($EXPECTED_DB_VERSION)"
            exit 1
        fi

        SCRIPT_DIR="$(realpath "$(dirname "$0")")"
        INSTALL_SCRIPT="install_db_$(date +%Y%m%d)_$EXPECTED_DB_VERSION.sh"

        echo "Dump database $PGDATABASE from $PGHOST:$PGPORT"
        mkdir -p "$DATA_DIR"

        echo "Dumping schema..."
        pg_dump --schema-only --format=p --section=pre-data > "$SCHEMA_PRE_DATA"
        pg_dump --schema-only --format=p --section=post-data > "$SCHEMA_POST_DATA"

        echo "Dumping data..."
        $PSQL <<EOF
        BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ;
        SET TRANSACTION READ ONLY;
        {psql_commands}
        COMMIT;
        EOF

        echo "Building install script..."
        INSTALL_SCRIPT_TMP="$INSTALL_SCRIPT.tmp"
        cp "$SCRIPT_DIR/{bootstrap_script}" "$INSTALL_SCRIPT_TMP"

        echo "Adding archive..."
        tar -czvf - \
            -C "$WORK_DIR" . \
            -C "$SCRIPT_DIR" "{build_script}" "{load_script}" "{bootstrap_script}" \
            >> "$INSTALL_SCRIPT_TMP"

        mv "$INSTALL_SCRIPT_TMP" "$INSTALL_SCRIPT"
        chmod +x "$INSTALL_SCRIPT"

        echo -e "\nWritten file: $INSTALL_SCRIPT\n"

        echo "All done."
    """
    psql_commands = "\n".join(
        # f"\\copy ({query}) TO '$DATA_DIR/{name}.csv' BINARY;"
        f"\\echo Dumping table {name}\n\\copy ({query}) TO '$DATA_DIR/{name}.csv' WITH CSV HEADER;"
        for name, query in queries.items()
    )
    return format_content(
        content,
        params={
            "script_version": SCRIPT_VERSION,
            "setup_psql": SETUP_PSQL,
            "setup_work_dir": SETUP_WORK_DIR,
            "bootstrap_script": BOOTSTRAP_SCRIPT,
            "build_script": BUILD_SCRIPT,
            "load_script": LOAD_SCRIPT,
            "psql_commands": psql_commands,
            "head": head,
        },
    )


def main():
    """Main entry point."""
    L.info("Updating scripts...")
    head = get_current_head()
    queries = get_queries()
    check_queries(queries)
    scripts_dir = Path(__file__).parent
    write_script(
        scripts_dir / BUILD_SCRIPT,
        content=_get_build_script_content(queries=queries, head=head),
    )
    write_script(scripts_dir / LOAD_SCRIPT, content=_get_load_script_content())
    write_script(scripts_dir / BOOTSTRAP_SCRIPT, content=_get_bootstrap_script_content())


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    main()
