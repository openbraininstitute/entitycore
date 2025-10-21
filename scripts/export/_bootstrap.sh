#!/bin/bash
# Automatically generated, do not edit!
set -euo pipefail

WORK_DIR=$(mktemp -d -t dump)
cleanup() {
    printf '\nCleaning up %s\n' "$WORK_DIR"
    rm -rf "$WORK_DIR"
}
trap cleanup EXIT
export WORK_DIR
export DATA_DIR="$WORK_DIR/data"
export SCHEMA_PRE_DATA="$DATA_DIR/schema_pre_data.sql"
export SCHEMA_POST_DATA="$DATA_DIR/schema_post_data.sql"


ARCHIVE_LINE=$(awk '/^__ARCHIVE_BELOW__/ { print NR + 1; exit 0; }' "$0")
tail -n +$ARCHIVE_LINE "$0" | tar -xzv -C "$WORK_DIR"
cd "$WORK_DIR"
./_load.sh
exit 0
__ARCHIVE_BELOW__
