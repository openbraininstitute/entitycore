import logging
from pathlib import Path
from textwrap import dedent

from sqlalchemy.orm import Mapper

from app.db.model import Base

L = logging.getLogger()

TABLES: dict[str, Mapper] = {
    mapper.class_.__tablename__: mapper
    for mapper in Base.registry.mappers
    if mapper.class_.__tablename__
}
SCRIPT_VERSION = 1
SCRIPT_HEADER = """
#!/bin/bash
set -euo pipefail

export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"
export PATH=/usr/pgsql-17/bin:$PATH

export PGUSER="${PGUSER:-entitycore}"
export PGHOST="${PGHOST:-127.0.0.1}"
export PGPORT="${PGPORT:-5433}"
export PGDATABASE="${PGDATABASE:-entitycore}"

PSQL="psql --echo-errors --set=ON_ERROR_STOP=on"

WORKDIR=$(mktemp -d -t dump)
DATE=$(date +%Y%m%d)

DUMP_ARCHIVE="${DUMP_ARCHIVE:-dump_db_$DATE.tar.gz}"
SCHEMA_PRE_DATA="$WORKDIR/schema_pre_data.sql"
SCHEMA_POST_DATA="$WORKDIR/schema_post_data.sql"

cleanup() {
    echo -e "\\nCleaning up $WORKDIR"
    rm -rf "$WORKDIR"
}
trap cleanup EXIT

if [[ -z "${PGPASSWORD:-}" ]]; then
    read -s -p "Enter password for postgresql://$PGUSER@$PGHOST:$PGPORT/$PGDATABASE: " PGPASSWORD
    echo
    export PGPASSWORD
fi
"""


def get_queries() -> dict[str, str]:
    callables = {
        # alembic
        "alembic_version": lambda t: _export_all(t, skip_check=True),
        # global tables
        "agent": _export_all,
        "brain_region": _export_all,
        "brain_region_hierarchy": _export_all,
        "annotation_body": _export_all,
        "consortium": _export_all,
        "datamaturity_annotation_body": _export_all,
        "etype_class": _export_all,
        "ion": _export_all,
        "license": _export_all,
        "mtype_class": _export_all,
        "organization": _export_all,
        "person": _export_all,
        "role": _export_all,
        "species": _export_all,
        "strain": _export_all,
        # tables with authorized_public
        "entity": _export_public,
        "activity": _export_public,
        # children of entity
        "analysis_software_source_code": lambda t: _export_child(t, "entity"),
        "brain_atlas": lambda t: _export_child(t, "entity"),
        "brain_atlas_region": lambda t: _export_child(t, "entity"),
        "cell_composition": lambda t: _export_child(t, "entity"),
        "circuit": lambda t: _export_child(t, "entity"),
        "electrical_cell_recording": lambda t: _export_child(t, "entity"),
        "electrical_recording_stimulus": lambda t: _export_child(t, "entity"),
        "emodel": lambda t: _export_child(t, "entity"),
        "scientific_artifact": lambda t: _export_child(t, "entity"),
        "reconstruction_morphology": lambda t: _export_child(t, "entity"),
        "experimental_bouton_density": lambda t: _export_child(t, "entity"),
        "experimental_neuron_density": lambda t: _export_child(t, "entity"),
        "experimental_synapses_per_connection": lambda t: _export_child(t, "entity"),
        "ion_channel_model": lambda t: _export_child(t, "entity"),
        "me_type_density": lambda t: _export_child(t, "entity"),
        "memodel": lambda t: _export_child(t, "entity"),
        "publication": lambda t: _export_child(
            t, "entity"
        ),  # TODO: publication will be global, see openbraininstitute/entitycore#313
        "simulation": lambda t: _export_child(t, "entity"),
        "simulation_campaign": lambda t: _export_child(t, "entity"),
        "simulation_result": lambda t: _export_child(t, "entity"),
        "single_neuron_simulation": lambda t: _export_child(t, "entity"),
        "single_neuron_synaptome": lambda t: _export_child(t, "entity"),
        "single_neuron_synaptome_simulation": lambda t: _export_child(t, "entity"),
        "subject": lambda t: _export_child(t, "entity"),
        # children of activity
        "simulation_execution": lambda t: _export_child(t, "activity"),
        "simulation_generation": lambda t: _export_child(t, "activity"),
        # other tables
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
        "scientific_artifact_publication_link": lambda t: _export_double_join(
            t, ("entity", "publication_id"), ("entity", "scientific_artifact_id")
        ),  # TODO: publication will be global, see openbraininstitute/entitycore#313
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


def _export_all(table: str, *, skip_check: bool = False) -> str:
    """Build and return the export query for global tables without authorized_public.

    Args:
        table: table name.
        skip_check: True to skip the validation.
    """
    if not skip_check:
        assert "authorized_public" not in TABLES[table].columns  # noqa: S101
    return f"""SELECT {table}.* FROM {table}"""  # noqa: S608


def _export_public(table: str) -> str:
    """Build and return the export query for base tables with authorized_public.

    Args:
        table: table name.
    """
    assert "authorized_public" in TABLES[table].columns  # noqa: S101
    return f"""SELECT {table}.* from {table} WHERE authorized_public IS true"""  # noqa: S608


def _export_child(table: str, parent: str) -> str:
    """Build and return the export query for children tables.

    Args:
        table: main table name.
        parent: parent table to join.
    """
    assert "authorized_public" in TABLES[table].columns  # noqa: S101
    return f"""
        SELECT {table}.* from {table}
        JOIN {parent} USING (id)
        WHERE {parent}.authorized_public IS true
        """  # noqa: S608


def _export_single_join(table: str, join: str, join_on: str) -> str:
    """Build and return the export query for linked tables (one to many).

    Args:
        table: main table name.
        join: table to join.
        join_on: the field in the main table to be used for the join.
    """
    assert "authorized_public" not in TABLES[table].columns  # noqa: S101
    return f"""
        SELECT {table}.* FROM {table}
        JOIN {join} AS t ON t.id={table}.{join_on}
        WHERE t.authorized_public IS true
        """  # noqa: S608


def _export_double_join(table: str, join_1: tuple[str, str], join_2: tuple[str, str]) -> str:
    """Build and return the export query for association tables (many to many).

    Args:
        table: main table name.
        join_1: tuple (join, join_on), where join is the first table to join,
            and join_on is the field in the main table to be used for the join.
        join_2: tuple (join, join_on), where join is the second table to join,
            and join_on is the field in the main table to be used for the join.
    """
    assert "authorized_public" not in TABLES[table].columns  # noqa: S101
    return f"""
        SELECT {table}.* FROM {table}
        JOIN {join_1[0]} AS t1 ON t1.id={table}.{join_1[1]}
        JOIN {join_2[0]} AS t2 ON t2.id={table}.{join_2[1]}
        WHERE t1.authorized_public IS true
        AND t2.authorized_public IS true
        """  # noqa: S608


def check_queries(queries: dict[str, str]) -> None:
    queries_set = set(queries)
    all_tables = set(Base.metadata.tables) | {"alembic_version"}
    if diff := all_tables - queries_set:
        L.warning("Missing tables in the configuration: %s", sorted(diff))
    if diff := queries_set - all_tables:
        L.warning("Extra tables in the configuration: %s", sorted(diff))


def write_content(filename, content: str, params) -> None:
    content = dedent(content)
    content = content.format(**params).lstrip()
    Path(filename).write_text(content, encoding="utf-8")
    Path(filename).chmod(mode=0o755)  # make the file executable


def write_dump_script(filename: str, queries: dict[str, str]) -> None:
    psql_commands = "\n".join(
        # f"\\copy ({query}) TO '$WORKDIR/{name}.csv' BINARY;"
        f"\\echo Dumping table {name}\n\\copy ({query}) TO '$WORKDIR/{name}.csv' WITH CSV HEADER;"
        for name, query in queries.items()
    )
    content = r"""
        {script_header}
        echo "DB DUMP - version {script_version}"
        echo "Dump database $PGDATABASE from $PGHOST:$PGPORT"
        echo "WORKDIR=$WORKDIR"

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

        echo "Building archive..."
        tar -czf "$DUMP_ARCHIVE" -C "$WORKDIR" .

        echo "All done."
    """
    write_content(
        filename,
        content,
        params={
            "script_version": SCRIPT_VERSION,
            "script_header": SCRIPT_HEADER,
            "psql_commands": psql_commands,
        },
    )


def write_load_script(filename: str) -> None:
    content = r"""
        {script_header}
        echo "DB LOAD - version {script_version}"
        echo "Restore database $PGDATABASE to $PGHOST:$PGPORT"
        echo "WORKDIR=$WORKDIR"

        tar -xzf "$DUMP_ARCHIVE" -C "$WORKDIR"

        echo "Dropping and recreating database..."
        dropdb --if-exists --force "$PGDATABASE"
        createdb "$PGDATABASE"

        echo "Restoring schema to destination DB..."
        $PSQL -f "$SCHEMA_PRE_DATA"

        echo "Importing data..."
        $PSQL <<EOF
        BEGIN;
        $(for FILE in "$WORKDIR"/*.csv; do
            TABLE=$(basename "$FILE" .csv)
            echo "\\echo Restoring table $TABLE"
            echo "\\copy $TABLE FROM '$FILE' WITH CSV HEADER;"
        done)
        COMMIT;
        EOF

        echo "Restoring schema to destination DB..."
        $PSQL -f "$SCHEMA_POST_DATA"

        echo "Running ANALYZE..."
        $PSQL -c "ANALYZE;"

        echo "All done."
    """
    write_content(
        filename,
        content,
        params={
            "script_version": SCRIPT_VERSION,
            "script_header": SCRIPT_HEADER,
        },
    )


def main():
    queries = get_queries()
    check_queries(queries)
    write_dump_script("scripts/dump.sh", queries)
    write_load_script("scripts/load.sh")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    main()
