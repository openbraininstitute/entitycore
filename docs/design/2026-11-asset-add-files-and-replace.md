# Add files to a directory asset, replace a file asset

- Status: Draft
- Date: 2026-11-19
- Author: @bilalesi
- Issues:
- Pull requests: [#771](https://github.com/openbraininstitute/entitycore/pull/771)

## Context

`Assets` are immutable today. Once created, a file's bytes never change and a directory never takes new files. That's a good default: an asset's `sha256_digest` is a safe reference, and S3 and the database can't drift apart.

but some data keeps growing after it's created:

- a folder that collects more files over time
- a document that must always show the newest text, under the same id and link

re-creating the asset each time doesn't work: the id and link change, and everything pointing at it breaks.

The first user is the ResearchLog ([record](2026-10-research-log-entity.md)). A research session keeps running after its log is created:

- Files that people or the agent add during the session go into the `research_log_files` directory, one at a time. So the directory must take new files after it's made.
- The logbook service syncs each page's text into the `research_log_document` asset. Readers should always get the newest text at the same link, so the document is replaced, not re-created.
- That sync runs from a background job with nobody signed in, on logs of every project. So it needs an admin route, used with the service's own account.

**In scope**: adding files to a directory asset, replacing the content of a file asset whose label opts in, and an admin route for replace. 
**Out of scope**: replacing or deleting single files inside a directory, replacing large (multipart) files, and making any existing label replaceable.

## Thoughts

Both endpoints hit the same hard problem: **S3 and Postgres don't share a transaction**. They solve it in different ways, because the bytes take different paths.

**Add files: the bytes never pass through the service.** The client uploads straight to S3 with a presigned URL, as `directory/upload` already does. So the service can't check anything at upload time. The only place to enforce rules is S3 itself, so the rules are signed into the URL. S3 then refuses any upload that breaks them.

**Replace: the bytes do pass through the service.** The document is small, and the row's `sha256_digest` and `size` must change together with the object. So the service writes to S3 inside the request, then updates the row. If the transaction doesn't commit, the S3 write is taken back

Two more rules apply to both:

- **Nothing is replaced unless a label opts in.** Adding files only creates new names. Replace only works on labels marked `is_replaceable`.
- **Concurrent writers must not lose data silently.** 
  - Add-files uses `If-None-Match: *` on S3. 
  - Replace uses `If-Match` plus a row lock.

### Add files to a directory

`POST /{entity_route}/{entity_id}/assets/{asset_id}/directory/files`

**Body**: up to 10 files (can be discussed), each `{path, size, sha256_digest}`. 
**Response**: one presigned PUT URL per file, plus the headers the PUT must send.

| Choice | Why |
|---|---|
| New names only. A name that exists gets 409 `ASSET_DIRECTORY_FILE_DUPLICATED`, with the taken names in `details.existing`. | Existing files never change, so anything that references them stays valid. |
| Two layers against duplicates: one S3 HEAD per asked name, then `If-None-Match: *` signed into the URL. | The HEAD answers 409 early, but it can race. The signed condition is the real guard: S3 refuses the second upload to the same name. |
| `Content-Length` and `x-amz-checksum-sha256` are signed into the URL. | S3 refuses an upload with another size or other bytes, so a URL can't be used to store something else. |
| These links are signed with SigV4. | the default presign signature here (SigV2) doesn't sign those headers, so S3 would ignore them. |
| Links last 15 min, not the usual 6 h. | a presigned URL is a permission that outlives the request: rights are checked at signing, not when the upload lands. With 6 h, an upload could land in a directory deleted or moved hours ago, and leave an orphan object. S3 checks expiry when the upload starts, so a slow upload still finishes: 15 min is the time to start, not to finish. A client that sends many big files one after another asks again for the ones it hasn't started in time. |
| Max 10 files per call. | each file costs one S3 HEAD inside the request, so the cap bounds the request time. |
| Max 5 GiB per file. | It's a single PUT, so it reuses the existing multipart part cap (`S3_MULTIPART_UPLOAD_MAX_PART_SIZE`), not a new setting. |
| Only finished directories made with `directory/upload`, on internal storage. Others get 409. | Multipart directories keep a row per file, and a file added here would have none. Open storage is public data the service doesn't write to. |
| The entity's `update_date` is bumped at signing time. |  |

### Replace a file asset

`PUT /{entity_route}/{entity_id}/assets/{asset_id}` with `If-Match: "<sha256 you read>"`

Same id, path, label and link. Only the bytes, `size`, `sha256_digest` and the update fields change. The response's `ETag` is the new digest.

| Choice | Why |
|---|---|
| Opt-in per label: `LabelRequirements.is_replaceable`, `False` by default. Today only `research_log_document` sets it. Any other asset, any directory and anything outside internal storage gets 409 `ASSET_NOT_REPLACEABLE`. | Immutability stays the rule. A label opts in only when readers must always get the newest content behind the same id. |
| Overwrite at the same S3 key. | An S3 PUT is atomic: a reader gets the old or the new content, never a mix. The link doesn't change. |
| Optimistic concurrency with the sha256: missing `If-Match` gets 428, malformed 422, stale 412 `ASSET_VERSION_MISMATCH` with the current digest in `details.sha256_digest`. | The digest is already on the row, so no version column and no migration. A stale caller can re-read and retry, and can't wipe a newer edit. |
| A row lock (`SELECT ... FOR UPDATE`) around the compare and the write. | Two replaces of the same asset run one after the other, and the second compares against what the first left. Without it, both could pass the `If-Match` check. |
| Same content type as the asset (422 otherwise). | A markdown document stays markdown. |
| On a public entity, the caller needs delete rights. | Overwriting published content is as destructive as deleting it. |
| Admin route: `PUT /admin/{entity_route}/{entity_id}/assets/{asset_id}`. Same rules, but it checks the admin role and not the project. | A background sync has no user token and works on logs of every project. |

### Undo when the database fails

The bucket has versioning on, so each PUT returns a `VersionId`. The service registers an undo on the request's transaction:

- commit: the undo is dropped, the write stays
- rollback, failed commit, or session closed without commit: `delete_object(VersionId=ours)`, and the previous version is current again

It deletes exactly the version it wrote. If someone wrote after it, theirs stays current. 

### Small fixes that come with it

- Private downloads set `Content-Type` on the link, so old files saved without a type download right. S3 only accepts that on a SigV4-signed link, so private download links move to SigV4. Open data links aren't signed and keep the stored type.
- Upload `meta` is read as JSON text, so it validates.

## Consequences

- Clients of add-files must send the returned headers exactly as given: they're part of the signature.
- A file sent as a bare path (no size or sha256) gets a URL with no checks: two uploads to the same new name can both land, and the last one wins. Kept for callers that can't hash before uploading.
- A bucket without versioning can't undo a replace. The service logs an error. Every bucket in use (production, docker, tests) has versioning on.
- If the undo call itself fails, it's logged. The row then has the old digest and the object the new content, until the next replace.
- Readers may briefly see the new content before the transaction commits.
- An add-files link that's never used still bumps the entity's `update_date`.
- A write made inside a savepoint is kept once the savepoint is released, even if an outer transaction rolls back later. No route writes to S3 inside a savepoint today.
- Private download links change from SigV2 to SigV4. Stored objects aren't touched. No database migration.

