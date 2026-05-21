# Multipart Upload

Multipart upload allows uploading large files to S3 in multiple parts using presigned URLs.
This is the recommended approach for files that exceed the direct upload size limit.

There are two variants:
- **Single file multipart upload** — for uploading a single large file as an asset.
- **Directory multipart upload** — for uploading multiple files as a directory asset, where each file is uploaded via multipart.

## Single File Multipart Upload

### Endpoints

```
POST /{entity_type}/{entity_id}/assets/multipart-upload/initiate
POST /{entity_type}/{entity_id}/assets/{asset_id}/multipart-upload/complete
```

### Flow

1. **Initiate** — The client sends a request with the file metadata (filename, filesize, sha256_digest, content_type, label, preferred_part_count). The server:
   - Validates the filename, filesize, and content type.
   - Creates an asset record in the database with status `UPLOADING`.
   - Initiates a multipart upload on S3.
   - Returns the asset metadata along with presigned URLs for each part.

2. **Upload parts** — The client uploads each part directly to S3 using the presigned URLs returned in step 1. Each part must match the `part_size` indicated in the response (except possibly the last part).

3. **Complete** — The client calls the complete endpoint. The server:
   - Verifies that all expected parts have been uploaded.
   - Verifies that the total uploaded size matches the declared filesize.
   - Assembles the parts into the final S3 object.
   - Updates the asset status to `CREATED`.

### Cancellation

If the upload needs to be cancelled, the client should delete the asset using the standard asset deletion endpoint. This aborts the multipart upload on S3 and removes the asset record.

### Example

```
# 1. Initiate
POST /cell-morphology/{entity_id}/assets/multipart-upload/initiate
{
    "filename": "large-morph.swc",
    "filesize": 157286400,
    "sha256_digest": "abcdef...",
    "label": "morphology",
    "content_type": "application/swc",
    "preferred_part_count": 10
}

# Response
{
    "id": "<asset_id>",
    "status": "uploading",
    "full_path": "...",
    "upload_meta": {
        "part_size": 15728640,
        "parts": [
            {"part_number": 1, "url": "https://s3..."},
            {"part_number": 2, "url": "https://s3..."},
            ...
        ]
    },
    ...
}

# 2. Upload each part using the presigned URLs (PUT requests directly to S3)

# 3. Complete
POST /cell-morphology/{entity_id}/assets/{asset_id}/multipart-upload/complete

# Response
{
    "id": "<asset_id>",
    "status": "created",
    ...
}
```

## Directory Multipart Upload

For directories containing multiple files, each file is uploaded via its own multipart upload session. The directory is represented as a parent asset with child assets for each file.

### Endpoints

```
POST /{entity_type}/{entity_id}/assets/directory/multipart-upload/initiate
POST /{entity_type}/{entity_id}/assets/{asset_id}/directory/multipart-upload/complete
```

### Flow

1. **Initiate** — The client sends a request with the directory name, label, and a list of files (each with filename, filesize, sha256_digest, preferred_part_count). The server:
   - Creates a parent directory asset with status `UPLOADING`.
   - For each file, creates a child asset with status `UPLOADING` and `parent_id` pointing to the parent.
   - Initiates a multipart upload on S3 for each child file.
   - Returns the parent asset metadata and presigned URLs for all parts of all files.

2. **Upload parts** — The client uploads each part of each file directly to S3 using the presigned URLs.

3. **Complete** — The client calls the complete endpoint with the parent asset ID. The server:
   - Verifies and completes the multipart upload for each child asset.
   - Updates the parent directory asset status to `CREATED`.

### Key differences from single file upload

- The `directory_name` must be a single path component (no nesting).
- File paths within the directory are relative to the directory root and can be nested (e.g., `subdir/file.txt`).
- Child assets use the label `directory_child` and are not returned in the entity's asset listing (only the parent directory is listed).
- Content type restrictions are relaxed for directory children:
    - if content_type is specified in the request, then it's preserved;
    - if content_type isn't specified, then it's determined from the extension;
    - if the resulting content_type isn't a valid `ContentType`, then it falls back to `application/octet-stream`.
- Deleting the parent directory asset cascades to all children and aborts their multipart uploads.

### Cancellation

Delete the parent directory asset. This cascades to all child assets and aborts all in-progress multipart uploads.

### Example

```
# 1. Initiate
POST /circuit/{entity_id}/assets/directory/multipart-upload/initiate
{
    "directory_name": "my-circuit-data",
    "label": "sonata_circuit",
    "meta": {"version": "1.0"},
    "files": [
        {
            "filename": "nodes.h5",
            "filesize": 52428800,
            "sha256_digest": "abc...",
            "preferred_part_count": 5
        },
        {
            "filename": "edges/chemical.h5",
            "filesize": 104857600,
            "sha256_digest": "def...",
            "preferred_part_count": 10
        }
    ]
}

# Response
{
    "asset": {
        "id": "<parent_asset_id>",
        "path": "my-circuit-data",
        "is_directory": true,
        "status": "uploading",
        ...
    },
    "files": [
        {
            "id": "<child_asset_id_1>",
            "path": "my-circuit-data/nodes.h5",
            "status": "uploading",
            "upload_meta": {
                "part_size": 10485760,
                "parts": [
                    {"part_number": 1, "url": "https://s3..."},
                    ...
                ]
            },
            ...
        },
        {
            "id": "<child_asset_id_2>",
            "path": "my-circuit-data/edges/chemical.h5",
            "status": "uploading",
            "upload_meta": {
                "part_size": 10485760,
                "parts": [
                    {"part_number": 1, "url": "https://s3..."},
                    ...
                ]
            },
            ...
        }
    ]
}

# 2. Upload each part of each file using the presigned URLs

# 3. Complete
POST /circuit/{entity_id}/assets/{parent_asset_id}/directory/multipart-upload/complete

# Response
{
    "id": "<parent_asset_id>",
    "status": "created",
    "is_directory": true,
    ...
}
```

## Comparison: Directory Upload vs Directory Multipart Upload

| Feature | Directory Upload | Directory Multipart Upload |
|---------|-----------------|---------------------------|
| Endpoint | `.../assets/directory/upload` | `.../assets/directory/multipart-upload/initiate` |
| Upload method | Single presigned PUT per file | Multipart upload per file |
| File size limit | Limited by presigned URL PUT | Up to `S3_MULTIPART_UPLOAD_MAX_SIZE` per file |
| Child tracking | Files not registered in DB | Each file registered as child asset |
| Completion | Implicit (no complete step) | Explicit complete endpoint required |
| Deletion cleanup | Files on S3 not auto-deleted ([#256](https://github.com/openbraininstitute/entitycore/issues/256)) | Children deleted on cascade, S3 cleanup via events |
