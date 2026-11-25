# Add files to a directory asset

- Status: Implemented
- Date: 2026-11-25
- Author: @bilalesi
- Issues:
- Pull requests: [#771](https://github.com/openbraininstitute/entitycore/pull/771) (discussion, first version), [#777](https://github.com/openbraininstitute/entitycore/pull/777)

## Context

A directory asset never takes new files after `directory/upload` creates it. The research log needs a folder that grows. During a research session, people and the agent add files one at a time to the `research_log_files` directory.

The files can be large. The web app accepts files up to 100 MB. The agent saves files up to 5 GiB. The service's own upload route, `POST /assets`, accepts at most 150 MB (`API_ASSET_POST_MAX_SIZE`).

In scope:

- Adding new files to a finished directory made by `directory/upload`, on internal storage.

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
| These URLs use SigV4. | botocore presigns S3 URLs with SigV2 by default. SigV2 does not sign those headers, so S3 would ignore them. |
| The SigV4 client signs for the public host, `S3_PRESIGNED_URL_NETLOC` when set. | SigV4 signs the host. Rewriting the host after signing, as the other presigned URLs do, would break the signature. |
| One S3 HEAD per asked name answers 409 `ASSET_DIRECTORY_FILE_DUPLICATED` early, with the taken names in `details.existing`. | It gives a clear error before any upload. It can race, so the signed `If-None-Match` is the real guard. |
| The URLs last 15 minutes, not the usual 6 hours. | The service checks write access when it signs. A short window keeps a late upload out of a directory deleted or moved since. S3 checks expiry when the upload starts, so a slow upload of a large file still finishes. |
| At most 10 files per request. | Each file costs one S3 HEAD inside the request, so the cap bounds the request time. |
| At most 5 GiB per file. | One PUT holds at most 5 GiB. The limit reuses `S3_MULTIPART_UPLOAD_MAX_PART_SIZE`. |
| Every file must send `size` and `sha256_digest`. | Each URL then carries all three checks. All current callers hash the file before they ask for a URL. |

## Alternatives considered

- Upload through the service with `put_object(IfNoneMatch="*", ChecksumAlgorithm="SHA256")`. This needs no presigning and no header contract. The service's upload path accepts at most 150 MB, and the agent saves files up to 5 GiB, so it cannot carry every file.
- Plain presigned URLs, as `directory/upload` uses, plus the HEAD check. They need no SigV4 client and no headers. S3 would not check the size or the bytes, and two uploads to one name would both land, with the last one kept. The agent's save path refuses a URL that does not make S3 check the bytes.
- Allow a bare path without size and sha256. No caller sends one, and its URL would carry no check.

## Consequences

- A client must send the returned headers exactly as given. They are part of the signature.
- An unused URL leaves nothing behind. A URL used after 15 minutes is refused, and the client asks again.
- The S3 mock used in the tests, moto, enforces `If-None-Match` but not `x-amz-checksum-sha256`. The tests cover the signed headers, the 412 on a second upload, and the 409. They do not cover a refused checksum.
