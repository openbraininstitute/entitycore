# Replace the content of a file asset

- Status: Implemented
- Date: 2026-11-25
- Author: @bilalesi
- Issues:
- Pull requests: [#771](https://github.com/openbraininstitute/entitycore/pull/771) (discussion, first version), [#776](https://github.com/openbraininstitute/entitycore/pull/776)

## Context

Assets are immutable today: once created, a file's bytes never change. That's a good default: an asset's `sha256_digest` is a safe reference, and S3 and the database can't drift apart.

The research log document is the exception. The logbook service syncs each page's text into the `research_log_document` asset, and readers should always get the newest text at the same id and link. Re-creating the asset on every sync changes the id and the link, and breaks everything pointing at it.

The sync runs as a background job with no user signed in, on logs of every project, so it uses an admin route with the service's own account.

**In scope**: replacing the content of a small file asset whose label opts in, through the admin route.
**Out of scope**: a user route (no caller yet), directories, large (multipart) files, making any other label replaceable, and adding files to a directory asset (a separate change).

## Decision

`PUT /admin/{entity_route}/{entity_id}/assets/{asset_id}` with the file and `If-Match: "<sha256 you read>"`. Same id, path, label and link; only the bytes, `size`, `sha256_digest`, `update_date` and `updated_by` of the asset change. The response's `ETag` is the new digest.

| Choice | Why |
|---|---|
| Opt-in per label: `LabelRequirements.is_replaceable`, `False` by default. Only `research_log_document` sets it. Any other label, any directory and anything outside internal storage gets 409 `ASSET_NOT_REPLACEABLE`. | Immutability stays the rule. A label opts in only when readers must always get the newest content behind the same id. |
| Overwrite at the same S3 key. | A single S3 PUT is atomic: a reader gets the old or the new content, never a mix. The link doesn't change. |
| Optimistic concurrency on the sha256: no `If-Match` gets 428, a malformed one 422, a stale one 412 `ASSET_VERSION_MISMATCH` with the current digest in `details.sha256_digest`. | The digest is already on the row, so there's no version column and no migration. A stale caller re-reads and retries, and can't wipe a newer edit. |
| A row lock (`SELECT ... FOR UPDATE`) around the compare and the write. | Two replaces of the same asset run one after the other, and the second compares against what the first wrote. Without it, both could pass the `If-Match` check. |
| Same content type as the asset (422 otherwise). | A markdown document stays markdown. |
| Admin route only. | The sync is the only caller, and it works on logs of every project. |

Two small upload fixes come with it, since replace uses the same path:

- Single-part uploads store the file's `Content-Type` on the S3 object. Before, S3 stored `binary/octet-stream`.
- The upload routes read `meta` as JSON text. A multipart form only carries strings and files, so the old `dict` field refused every `meta` with 422.

## Alternatives considered

- **Undo the S3 write when the transaction fails** (delete the version just written, so the old one is current again). Not needed for the sync: a failed sync keeps the page marked and retries with the digest it last read, which still matches the row, so the next replace puts the row and the object back in line. It can be added later if another caller needs it.
- **A user route with the same rules.** No caller today.
- **A version column on the asset.** The sha256 already identifies the content, and a column needs a migration.

## Consequences

- If the transaction fails after the S3 PUT, the object has the new content and the row the old digest and size, until the next replace. The sync retries on its own.
- Objects uploaded before this change keep their stored type (`binary/octet-stream`). No migration.

## Follow-ups

- Add files to a directory asset (separate pull request).
