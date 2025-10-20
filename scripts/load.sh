#!/bin/bash
# Automatically generated, do not edit!

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
    echo -e "\nCleaning up $WORKDIR"
    rm -rf "$WORKDIR"
}
trap cleanup EXIT

if [[ -z "${PGPASSWORD:-}" ]]; then
    read -s -p "Enter password for postgresql://$PGUSER@$PGHOST:$PGPORT/$PGDATABASE: " PGPASSWORD
    echo
    export PGPASSWORD
fi

echo "DB LOAD - version 1"
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
