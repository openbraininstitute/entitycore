#!/usr/bin/env bash
#
# Runbook: manually move large assets in S3, then let the publish endpoint
# reconcile the DB and finish the (now no-op) moves — without hitting the ALB timeout.
#
# Context (verified against the code):
#   - move_file()/move_directory() detect an already-moved object via
#     source-HEAD -> 404 AND destination-HEAD -> exists, and treat it as success
#     (no copy, no delete). See app/utils/s3.py.
#   - The publish query (app/service/publish.py) selects ALL assets under the
#     source prefix, INCLUDING directory_child rows and the parent directory row,
#     and updates their full_path from private/ -> public/ regardless of how many
#     files were physically moved. So a full manual move => the endpoint becomes
#     a pure DB reconciliation with no large in-request copy.
#   - Therefore: MOVE (copy + DELETE source) everything, then call the endpoint.
#
# IMPORTANT
#   - This deletes source objects. Bucket versioning is ENABLED, so the delete
#     creates delete markers and previous versions remain recoverable by VersionId
#     until you prune them. That is your rollback path.
#   - AWS identity: use the EntityCoreStorageAdmin SSO permission set. This is an
#     IAM Identity Center permission set (role AWSReservedSSO_EntityCoreStorageAdmin_*),
#     NOT a plain assumable role, and NOT the bastion instance role (which lacks
#     s3 write/list on the bucket). Its policy grants CopyObject/UploadPartCopy/
#     DeleteObject(s)/PutObject/Get*/List* on entitycore-data-{staging,production}.
#     The move is server-side S3->S3 in us-east-1, so run it from any machine with
#     SSO configured (e.g. your laptop) — bandwidth is irrelevant.
#   - The script STOPS for manual confirmation before any destructive step and
#     before the real (dry_run=false) publish call.
#
# Usage:
#   1. Ensure ~/.aws/config has an SSO profile for the permission set, e.g.:
#        [profile entitycore-storage-admin]
#        sso_session = obi
#        sso_account_id = 671250183987
#        sso_role_name = EntityCoreStorageAdmin
#        region = us-east-1
#        output = json
#        [sso-session obi]
#        sso_start_url = https://openbraininstitute.awsapps.com/start/
#        sso_region = us-east-1
#        sso_registration_scopes = sso:account:access
#   2. aws sso login --sso-session obi
#   3. Fill in the CONFIG section below (or export the env vars before running).
#      Set OBI_ENV=production (or staging). The entitycore admin JWT is minted
#      just-in-time via `obi-auth get-token -e $OBI_ENV` immediately before each
#      API call, so a long STEP 3 move cannot cause the token to expire before
#      STEP 5/6. (obi-auth reads a local cache or opens a browser as needed.)
#      Alternatively pre-set AUTH_TOKEN to reuse a specific token.
#   4. AWS_PROFILE=entitycore-storage-admin OBI_ENV=production \
#        bash scripts/publish_project_manual_move.sh
#
set -euo pipefail

########################################
# CONFIG — edit these or export as env #
########################################

BUCKET="${BUCKET:-entitycore-data-production}"
REGION="${REGION:-us-east-1}"

# AWS identity: use the EntityCoreStorageAdmin SSO permission set.
# Configure a profile in ~/.aws/config (see header/README) and `aws sso login` first.
# Exported so every `aws` call below uses it without repeating --profile.
AWS_PROFILE="${AWS_PROFILE:-entitycore-storage-admin}"
export AWS_PROFILE
export AWS_REGION="${REGION}"

# S3 layout: <prefix>/<vlab_id>/<project_id>/assets/...
VLAB_ID="${VLAB_ID:-5f8376bf-b84f-4188-8ef5-e1df3d7529b4}"
PROJECT_ID="${PROJECT_ID:-f04e3094-f342-4664-b4ed-f2c88e7d588e}"

# entitycore admin API. The publish endpoint is POST /admin/publish-project/{project_id}
# Confirm the exact base URL and auth for production before running.
API_BASE_URL="${API_BASE_URL:-https://cell-a.openbraininstitute.org/api/entitycore}"

# Environment for obi-auth token minting: "production" or "staging".
OBI_ENV="${OBI_ENV:-production}"
# Optional: pre-supplied bearer token. If set, it is used as-is and obi-auth is
# NOT called. Leave empty to mint a FRESH token just-in-time before each API call
# (recommended — avoids expiry while the long STEP 3 move runs).
AUTH_TOKEN="${AUTH_TOKEN:-}"

# Derived prefixes (note the trailing slash — required to avoid sibling-prefix matches)
SRC_PREFIX="private/${VLAB_ID}/${PROJECT_ID}/assets/"
DST_PREFIX="public/${VLAB_ID}/${PROJECT_ID}/assets/"

SRC_URI="s3://${BUCKET}/${SRC_PREFIX}"
DST_URI="s3://${BUCKET}/${DST_PREFIX}"

PUBLISH_URL="${API_BASE_URL}/admin/publish-project/${PROJECT_ID}"

########################################
# Helpers                              #
########################################

confirm() {
  # $1 = prompt
  local reply
  read -r -p "$1 [type 'yes' to continue]: " reply
  if [[ "$reply" != "yes" ]]; then
    echo "Aborted."
    exit 1
  fi
}

hr() { printf '%.0s-' {1..72}; echo; }

# Mint (or reuse) a bearer token for the entitycore admin API.
# If AUTH_TOKEN is preset, reuse it; otherwise fetch a FRESH token via obi-auth.
# Called just-in-time immediately before each API call so a long STEP 3 move
# cannot cause the token to expire before STEP 5/6.
get_token() {
  if [[ -n "${AUTH_TOKEN}" ]]; then
    printf '%s' "${AUTH_TOKEN}"
    return 0
  fi
  local tok
  tok=$(obi-auth get-token -e "${OBI_ENV}") || {
    echo "ERROR: obi-auth get-token -e ${OBI_ENV} failed." >&2
    return 1
  }
  if [[ -z "${tok}" ]]; then
    echo "ERROR: obi-auth returned an empty token." >&2
    return 1
  fi
  printf '%s' "${tok}"
}

# POST the publish endpoint with a freshly-minted token. $1 = true|false (dry_run).
# Writes response to $2. Fails clearly on HTTP errors.
publish_call() {
  local dry_run="$1" outfile="$2" token http_code
  token=$(get_token) || return 1
  http_code=$(curl -sS -o "${outfile}" -w '%{http_code}' -X POST \
    "${PUBLISH_URL}?dry_run=${dry_run}" \
    -H "Authorization: Bearer ${token}" \
    -H "accept: application/json")
  echo "HTTP ${http_code}"
  cat "${outfile}"
  echo
  if [[ "${http_code}" != "200" ]]; then
    echo "ERROR: publish call returned HTTP ${http_code} (expected 200)." >&2
    if [[ "${http_code}" == "401" || "${http_code}" == "403" ]]; then
      echo "Auth failed — token may be expired/insufficient. Re-run 'obi-auth get-token -e ${OBI_ENV}'." >&2
    fi
    return 1
  fi
}

########################################
# Step 0 — sanity echo of config       #
########################################
hr
echo "BUCKET      : ${BUCKET}"
echo "REGION      : ${REGION}"
echo "AWS_PROFILE : ${AWS_PROFILE}"
echo "OBI_ENV     : ${OBI_ENV}  (obi-auth token environment)"
echo "VLAB_ID     : ${VLAB_ID}"
echo "PROJECT_ID  : ${PROJECT_ID}"
echo "SRC_URI     : ${SRC_URI}"
echo "DST_URI     : ${DST_URI}"
echo "PUBLISH_URL : ${PUBLISH_URL}"
hr

# Verify AWS identity is the EntityCoreStorageAdmin permission set (write access).
echo "Verifying AWS identity..."
CALLER_ARN=$(aws sts get-caller-identity --query 'Arn' --output text 2>&1) || {
  echo "Failed to get caller identity. Did you run 'aws sso login --sso-session obi'?"
  echo "Output: ${CALLER_ARN}"
  exit 1
}
echo "  Caller: ${CALLER_ARN}"
if [[ "${CALLER_ARN}" != *"EntityCoreStorageAdmin"* ]]; then
  echo "WARNING: caller is NOT the EntityCoreStorageAdmin role."
  echo "Read-only or Terraform roles cannot perform the move/delete steps."
  confirm "Continue anyway?"
fi
hr
confirm "Config and identity correct?"

########################################
# Step 1 — baseline listing (source)   #
########################################
hr
echo "STEP 1: Baseline source listing (before move)"
aws s3 ls "${SRC_URI}" --recursive --summarize --region "${REGION}"
hr
echo "Record the 'Total Objects' and 'Total Size' above."
confirm "Baseline looks right?"

########################################
# Step 2 — dry-run publish (before)    #
########################################
hr
echo "STEP 2: dry_run=true publish call (before manual move) — captures the plan"
publish_call true /tmp/publish_dryrun_before.json
hr
echo "Review /tmp/publish_dryrun_before.json (asset/file counts, move sizes)."
echo "NOTE: counts/sizes may be inflated because directory_child rows are counted"
echo "      in addition to the parent directory listing. This is a known cosmetic"
echo "      issue and does not affect correctness of the update."
confirm "Dry-run (before) looks right?"

########################################
# Step 3 — the recursive MOVE          #
########################################
hr
echo "STEP 3: DESTRUCTIVE — recursive move of ALL assets private/ -> public/"
echo "This copies (server-side, multipart for large objects) then DELETES sources."
echo "Sources become delete markers (versioning enabled); previous versions kept."
echo "From: ${SRC_URI}"
echo "To  : ${DST_URI}"
hr
confirm "Proceed with the recursive move?"

aws s3 mv "${SRC_URI}" "${DST_URI}" \
  --recursive \
  --region "${REGION}" \
  --only-show-errors
echo "Move command finished."

########################################
# Step 4 — verify move                 #
########################################
hr
echo "STEP 4: Verify destination and source after move"
echo "Destination (should list the expected number of objects and bytes):"
aws s3 ls "${DST_URI}" --recursive --summarize --region "${REGION}"
hr
echo "Source current versions (should be EMPTY — only delete markers remain):"
aws s3 ls "${SRC_URI}" --recursive --summarize --region "${REGION}" || true
hr
confirm "Destination complete and source empty?"

########################################
# Step 5 — dry-run publish (after)     #
########################################
hr
echo "STEP 5: dry_run=true publish call (after move) — should report ~0 moves,"
echo "        because every asset is already at its public/ key."
publish_call true /tmp/publish_dryrun_after.json
hr
echo "Review /tmp/publish_dryrun_after.json — move_assets_result sizes should be ~0"
echo "(the endpoint sees sources as already-moved), and completed should be true."
confirm "Dry-run (after) shows no real copy work remaining?"

########################################
# Step 6 — REAL publish                #
########################################
hr
echo "STEP 6: REAL publish (dry_run=false) — flips entity visibility to public and"
echo "        updates full_path for the parent directory asset, all directory_child"
echo "        rows, and single-file assets. No large copy happens (all already moved)."
hr
confirm "Execute the REAL publish now?"

publish_call false /tmp/publish_real.json
hr
echo "Review /tmp/publish_real.json — expect completed=true and message 'made public'."
echo
echo "POST-CHECKS (do manually):"
echo "  - Confirm entities are public and a directory/file asset is downloadable."
echo
echo "OLD VERSIONS:"
echo "  The 'aws s3 mv' in STEP 3 deleted the source objects by creating delete"
echo "  markers; the previous versions still exist under:"
echo "    ${SRC_PREFIX}"
echo "  This is harmless for correctness (it is your rollback material) and can be"
echo "  left in place. 'aws s3 mv' / 'aws s3 rm' CANNOT hard-delete these versions;"
echo "  version cleanup is always a separate operation. When you decide on a policy,"
echo "  options are:"
echo "    - S3 Lifecycle rule: NoncurrentVersionExpiration + ExpiredObjectDeleteMarker"
echo "      (bulk, async ~1 day; check the bucket lifecycle is not Terraform-managed first)"
echo "    - S3 console: 'Show versions', then delete under the prefix (fine for small counts)"
echo "    - s3api list-object-versions + delete-objects (scripted, for large/repeated cleanups)"
hr
echo "Done."
