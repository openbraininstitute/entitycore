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
| A label opts in with `LabelRequirements.is_replaceable`, which defaults to `False`. The requirement that opts in must match the asset's content type. Only `research_log_document` sets it, and only a file requirement may set it. Any other label, any directory and any asset outside internal storage gets 409 `ASSET_NOT_REPLACEABLE`, with a message for each cause. | Immutability stays the rule. A label opts in only when readers must always get the newest content behind the same id. |
| The service overwrites the object at the same S3 key. | A single S3 PUT is atomic. A reader that reads the object in one GET gets the old content or the new content, never a mix. The link does not change. |
| Before the PUT, the service reads the version id of the current object (`head_object`). After the PUT, it deletes that one version: one HEAD and one delete per replace, so the key keeps one version. The row lock keeps other replaces of the asset out in between. | Publish and unpublish move an object by deleting only its current version. With old versions left, the previous content would become current again at the old key, served from a key no asset lists, and the lifecycle rule would never expire it. The lifecycle rule also keeps the 3 newest old versions with no time limit (`newer_noncurrent_versions = 3`), so removed text would stay. Listing the versions instead needs `s3:ListBucketVersions`, which the service's task role in AWS doesn't have (the IAM policy simulator rates it `implicitDeny`); HEAD needs only `s3:GetObject`, and the delete `s3:DeleteObjectVersion`, both granted. A key re-used after a delete holds an older version behind a delete marker: deleting only the previous version keeps the marker in front, so publish doesn't bring the older data back (checked on Floci's S3). |
| Optimistic concurrency uses the sha256. A dependency of the route validates `If-Match` before any database read: a missing or malformed `If-Match`, or more than one `If-Match` field, gets 422. An asset with no digest gets 409 `ASSET_NOT_REPLACEABLE`. A stale one gets 412 `ASSET_VERSION_MISMATCH`, with the current digest in `details.sha256_digest`. | The row already stores the digest, so the change needs no version column and no migration. A stale caller reads again and retries. It cannot overwrite a newer edit. |
| A `SELECT ... FOR UPDATE` row lock covers the compare and the write. | Two replaces of the same asset run one after the other. The second compares its `If-Match` with the digest the first wrote. Without the lock, both could pass the check. |
| The new file must have the asset's content type. Any other type gets 422. | A markdown document stays markdown. |
| An empty file is accepted. | The logbook clears a page's document this way, so the document doesn't keep text that was removed. The id and link stay. |
| The asset of a public entity gets 403 `ENTITY_FORBIDDEN`. The entity is read again under the row lock. | Published content stays as published, as for adding files to a directory. Files under `public/` are copied out as open data every night. A publish that runs during a replace is seen. |
| Only the admin route exists. | The sync is the only caller, and it works on logs of every project. |

Replace uses the single-part upload path, so two fixes to that path come with it:

- Single-part uploads store the file's `Content-Type` on the S3 object. Before this change, S3 stored `binary/octet-stream`.
- The upload routes read `meta` as JSON text. A multipart form carries only strings and files, so the old `dict` field refused every `meta` with 422.

## Alternatives considered

- List and delete every old version after the PUT (the first version of this change). It also cleans up versions left by an earlier failed delete, but needs `s3:ListBucketVersions` on the task role, a policy change deployed before entitycore. With the policy as it is, every replace answered 500.
- Delete every version of the source in `move_file`, at publish time. Old versions would stay while the entity is private, but every file of every publish would cost one more S3 list. Nothing reads the old versions.
- Undo the S3 write when the transaction fails, by putting the old content back. The replace deletes the old version, so the undo would have to keep it first. The sync does not need it. When a sync fails, the logbook service keeps the page marked and retries with the digest it last read. That digest still matches the row, so the next replace puts the row and the object back in line. A later change can add the undo if another caller needs it.
- A user route with the same rules. No caller needs one today.
- A version column on the asset. The sha256 already identifies the content, and a column needs a migration.

## Consequences

- If the transaction fails after the S3 PUT, the object holds the new content and the row holds the old digest and size. The next replace fixes both, and the sync retries on its own.
- Objects uploaded before this change keep their stored type, `binary/octet-stream`. The change runs no migration.
- Once a project is published, the sync gets 403 for its logs and can't update them.
- A replace keeps no old content in S3. Text a replace removed can't be restored from S3.
- Limit: if the delete of the previous version fails, the replace still answers 200 (the new content is saved and the row follows it) and the error is logged. That version stays behind, and a publish brings it back at the private key, where no asset lists it. Answering 500 would not help: the retry deletes only the version of the failed try. Upgrade: grant `s3:ListBucketVersions` and list the old versions after the PUT.
- Limit: a reader that reads one object in several `Range` requests, such as entitysdk's `HttpFile`, can get blocks of two versions if a replace lands between two reads. Upgrade: such readers send `If-Range` with the ETag of their first read.

## Follow-ups

- Add files to a directory asset, in a separate pull request.
