# Add files to a directory asset

- Status: Implemented
- Date: 2026-11-25
- Author: @bilalesi
- Issues:
- Pull requests: [#771](https://github.com/openbraininstitute/entitycore/pull/771) (discussion, first version), [#777](https://github.com/openbraininstitute/entitycore/pull/777)

## Context

A directory asset never takes new files after `directory/upload` creates it. The research log needs a folder that grows. During a research session, people and the agent add files one at a time to the `research_log_files` directory. The research log is the first user. The endpoint works for any directory asset.

The files can be large. The web app accepts files up to 100 MB. The agent saves files up to 5 GiB. The service's own upload route, `POST /assets`, accepts at most 150 MB (`API_ASSET_POST_MAX_SIZE`).

In scope:

- Adding new files to a directory made by `directory/upload`, on internal storage, of a private entity.

Out of scope:

- Replacing or deleting a single file inside a directory.
- Directories made by multipart upload, and directories on open storage.

## Decision

`POST /{entity_route}/{entity_id}/assets/{asset_id}/directory/files` takes up to 10 files, each as `{path, size, sha256_digest}`. It answers with one presigned PUT URL per file and the headers each PUT must send.

The bytes go straight from the client to S3, as with `directory/upload`. The service never sees them, so it cannot check them at upload time. The rules are signed into the URL instead, and S3 refuses any upload that breaks them.

| Choice | Why |
|---|---|
| The service signs `If-None-Match: *` into each URL. | S3 refuses a second upload to the same name with 412, so an existing file is never replaced. A reference to a file stays valid. |
| The service signs `Content-Length` and `x-amz-checksum-sha256` into each URL. | S3 refuses an upload with another size or other bytes. A URL cannot store anything but the announced file. |
| The service signs `Content-Type`, guessed from the file extension. | The uploader can't store a file as `text/html` when its name says otherwise. Downloads serve the stored type. |
| These URLs use SigV4. | botocore presigns S3 URLs with SigV2 by default. SigV2 does not sign those headers, so S3 would ignore them. |
| The SigV4 client signs for the public host when `S3_PRESIGNED_URL_NETLOC` is set. Otherwise boto3 picks the endpoint, as for the storage client. | SigV4 signs the host. Rewriting the host after signing, as the other presigned URLs do, would break the signature. Without a custom endpoint, AWS gets the same virtual-hosted URLs as the other presigned URLs. |
| A public entity gets 403 `ENTITY_FORBIDDEN`. | Members can't delete the files of a public entity, so they must not add files they can't take back. Files under `public/` are also copied out as open data. |
| One S3 HEAD and one LIST per asked name answer 409 `ASSET_DIRECTORY_FILE_DUPLICATED` early, with the taken names in `details.existing`. A name is taken when it is a file, a folder, or has a file as one of its folders. | It gives a clear error before any upload, and keeps a file and a folder from sharing a name. The check can race, so the signed `If-None-Match` is the real guard against overwrites. |
| A path with control characters, or an S3 key over 1024 bytes, gets 422. | S3 or file systems refuse those names, so the URL could never be used. Before, the HEAD on such a key failed and the request answered 500. |
| The URLs last 15 minutes, not the usual 6 hours. | Write access is checked only when the service signs. A short window limits what a late upload can do. S3 checks expiry when the upload starts, so a slow upload of a large file still finishes. |
| At most 10 files per request. | Each file costs S3 calls inside the request, so the cap bounds the request time. |
| At most 5 GiB per file (`S3_SINGLE_PUT_MAX_SIZE`). | One PUT holds at most 5 GiB. |
| Every file must send `size` and `sha256_digest`. | Each URL then carries all the checks. All current callers hash the file before they ask for a URL. |

## Alternatives considered

- Upload through the service with `put_object(IfNoneMatch="*", ChecksumAlgorithm="SHA256")`. This needs no presigning and no header contract. The service's upload path accepts at most 150 MB, and the agent saves files up to 5 GiB, so it cannot carry every file.
- Plain presigned URLs, as `directory/upload` uses, plus the HEAD check. They need no SigV4 client and no headers. S3 would not check the size or the bytes, and two uploads to one name would both land, with the last one kept. The agent's save path refuses a URL that does not make S3 check the bytes.
- Allow a bare path without size and sha256. No caller sends one, and its URL would carry no check.
- Limit the endpoint to the `research_log_files` label. Left open in review: a generic endpoint lets other directories grow too.

## Consequences

- A client must send the returned headers exactly as given. They are part of the signature. The body needs a fixed `Content-Length`. A chunked upload gets 403.
- An unused URL leaves nothing behind. A URL used after 15 minutes is refused, and the client asks again. A URL can stop working sooner when the service's AWS keys rotate.
- Limit: a URL signed before a publish, a delete of the directory or of the entity still works for its 15 minutes. The upload lands at the old key and no asset lists it. If the directory is deleted and created again with the same name, the upload lands in the new directory, because the S3 path has no asset id. Upgrade: put the asset id in the directory's S3 path, or sweep the old prefix after the URLs expire.
- Limit: the URLs of `directory/upload` carry no `If-None-Match`, and the names they were made for are not stored. Such a URL can overwrite a file added here under the same name, within its 6 hours. Upgrade: sign `If-None-Match` into the `directory/upload` URLs too.
- The S3 mock used in the tests, moto, enforces `If-None-Match` but not the size, the checksum or the signature. The tests check the list of signed headers, the 412 on a second upload and the 409s. They do not show S3 refusing other bytes.
