#!/bin/bash
# Manually created, it can be edited.
set -euo pipefail

SYNC_OPTIONS="${SYNC_OPTIONS---dryrun}"
BUCKET_NAME="${BUCKET_NAME:-entitycore-data-staging}"
DST_DIR="${DST_DIR:-data/assets-sync}"
ARCHIVE="assets_${BUCKET_NAME}_$(date +%Y%m%d).tar.gz"

SRC_PATHS=(
    public/
)

printf "Sync public assets from s3://%s to %s with options: %s
WARNING! All the data might be overwritten or deleted!\n" \
  "$BUCKET_NAME" "$DST_DIR" "$SYNC_OPTIONS"
read -r -p "Press Enter to continue or Ctrl+C to cancel..."

if [[ -z "${AWS_PROFILE:-}" ]]; then
    read -r -p "Enter your AWS_PROFILE: " AWS_PROFILE
    echo
    export AWS_PROFILE
fi

echo "Logging in AWS with profile: $AWS_PROFILE"
aws sso login

mkdir -p "$DST_DIR"
for SRC_PATH in "${SRC_PATHS[@]}"; do
  aws s3 sync $SYNC_OPTIONS "s3://$BUCKET_NAME/$SRC_PATH" "$DST_DIR/$SRC_PATH"
done

tar -czf "$ARCHIVE" -C "$DST_DIR" .
echo -e "\nWritten file: $ARCHIVE\n"

echo "All done."
