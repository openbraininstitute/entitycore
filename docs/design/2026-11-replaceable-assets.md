# Replace the content of a file asset

- Status: Implemented
- Date: 2026-11-25
- Author: @bilalesi
- Issues:
- Pull requests: [#771](https://github.com/openbraininstitute/entitycore/pull/771) (discussion, first version), [#776](https://github.com/openbraininstitute/entitycore/pull/776)

## Context

Assets are immutable today. Once an asset exists, its bytes never change. That is a good default. An asset's `sha256_digest` stays a safe reference, and S3 and the database cannot drift apart.

The research log document is the exception. The logbook service syncs the text of each page into the `research_log_document` asset. Readers must always get the newest text at the same asset id and link. If the sync created a new asset each time, the id and the link would change, and every reference to the old id would break.

The sync runs as a background job with no signed-in user, and it works on logs of every project. It calls an admin route with the service's own account.

In scope:

- Replacing the content of a small file asset whose label opts in, through the admin route.

Out of scope:

- A user route. No caller needs one today.
- Directories and large multipart files.
- Making any other label replaceable.
- Adding files to a directory asset. A separate change covers it.

## Decision

`PUT /admin/{entity_route}/{entity_id}/assets/{asset_id}` takes the file and the header `If-Match: "<sha256 you read>"`. The asset keeps its id, path, label and link. The request changes only the bytes, `size`, `sha256_digest`, `update_date` and `updated_by` of the asset. The response's `ETag` is the new digest.

| Choice | Why |
|---|---|
| A label opts in with `LabelRequirements.is_replaceable`, which defaults to `False`. Only `research_log_document` sets it. Any other label, any directory and any asset outside internal storage gets 409 `ASSET_NOT_REPLACEABLE`. | Immutability stays the rule. A label opts in only when readers must always get the newest content behind the same id. |
| The service overwrites the object at the same S3 key. | A single S3 PUT is atomic. A reader gets the old content or the new content, never a mix. The link does not change. |
| Optimistic concurrency uses the sha256. A request without `If-Match` gets 428. A malformed `If-Match` gets 422. A stale one gets 412 `ASSET_VERSION_MISMATCH`, with the current digest in `details.sha256_digest`. | The row already stores the digest, so the change needs no version column and no migration. A stale caller reads again and retries. It cannot overwrite a newer edit. |
| A `SELECT ... FOR UPDATE` row lock covers the compare and the write. | Two replaces of the same asset run one after the other. The second compares its `If-Match` with the digest the first wrote. Without the lock, both could pass the check. |
| The new file must have the asset's content type. Any other type gets 422. | A markdown document stays markdown. |
| An empty file gets 422 `ASSET_INVALID_FILE`. | A sync that sends an empty body by mistake would erase the document. |
| The asset of a public entity gets 403 `ENTITY_FORBIDDEN`. The entity is read again under the row lock. | Published content stays as published, as for adding files to a directory. Files under `public/` are copied out as open data every night. A publish that runs during a replace is seen. |
| Only the admin route exists. | The sync is the only caller, and it works on logs of every project. |

Replace uses the single-part upload path, so two fixes to that path come with it:

- Single-part uploads store the file's `Content-Type` on the S3 object. Before this change, S3 stored `binary/octet-stream`.
- The upload routes read `meta` as JSON text. A multipart form carries only strings and files, so the old `dict` field refused every `meta` with 422.

## Alternatives considered

- Undo the S3 write when the transaction fails, by deleting the version the request wrote. The sync does not need it. When a sync fails, the logbook service keeps the page marked and retries with the digest it last read. That digest still matches the row, so the next replace puts the row and the object back in line. A later change can add the undo if another caller needs it.
- A user route with the same rules. No caller needs one today.
- A version column on the asset. The sha256 already identifies the content, and a column needs a migration.

## Consequences

- If the transaction fails after the S3 PUT, the object holds the new content and the row holds the old digest and size. The next replace fixes both, and the sync retries on its own.
- Objects uploaded before this change keep their stored type, `binary/octet-stream`. The change runs no migration.
- Once a project is published, the sync gets 403 for its logs and can't update them.
- Limit: the bucket is versioned, so each replace keeps the old content as a noncurrent version. The lifecycle rule keeps those for 90 days. The logbook syncs a page at most every 120 s while people edit it. Upgrade: tag replaceable objects on PUT and expire their old versions sooner with a tag-filtered lifecycle rule.

## Follow-ups

- Add files to a directory asset, in a separate pull request.
