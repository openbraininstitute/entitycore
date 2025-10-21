#!/bin/bash
# Automatically generated, do not edit!
set -euo pipefail
echo "DB LOAD (version 1 for db version 805fc8028f39)"


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
    echo "Error: psql not found in PATH, please set the correct PATH or the PSQL_BIN var."
    exit 1
fi

if [[ -z "${PGPASSWORD:-}" ]]; then
    read -r -s -p "Enter password for postgresql://$PGUSER@$PGHOST:$PGPORT/$PGDATABASE: " PGPASSWORD
    echo
    export PGPASSWORD
fi


echo "Restore database $PGDATABASE to $PGHOST:$PGPORT"

DATA_DIR="data"
SCHEMA_PRE_DATA="$DATA_DIR/schema_pre_data.sql"
SCHEMA_POST_DATA="$DATA_DIR/schema_post_data.sql"

if [[
    ! -f "${SCHEMA_PRE_DATA:-}" ||
    ! -f "${SCHEMA_POST_DATA:-}" ||
    ! -d "${DATA_DIR:-}"
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
