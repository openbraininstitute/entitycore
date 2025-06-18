# Files


## Functional requirements

- Any entity may be optionally associated with one or more assets.
- Assets are files or directories that are stored on S3.
- Assets belong to a specific project and entity.
- The assets can be organized in subfolders.
- When associating a directory, we don't register the single files in the directory and subdirectories.
- According to the associated entity, assets may be:
    - private (readable and writable only by a single project)
    - public (readable by any project, writable only by the owner project)
- We may want to be able to move entities and assets from private to public.
- We may want to be able to move entities and assets from public to private (only if not used).
- We may want to restrict writability in some cases. For example after the entity is published/released.
- To avoid complications, the path on S3 must be unique (we don't want multiple assets records pointing to the same file).
- There might be some cases in which people want to create an incomplete entity, then add files onto it later.
- Versions/revisions of entities and files are not required (to be discussed).
- Assets are identified by an id.
- (not specific to assets) Entities must have a unique id that can be used in citations. Examples:
    - `obi:reconstruction-morphology/27` (exposes the entity type and the internal numeric id)
    - `obi:27` (the id is globally unique even without the entity type)

## Asset management

### Asset creation

- Upload for small files can be done directly through the API (to be checked what limit to consider)
- Upload for big files should be done through delegation as proposed originally in the separate document "SBO Infrastructure Platform : Architecture to Manage Data in Lustre FSx and Nexus Integration" (TODO: copy it here).
  This flow can be used to allow bbp-workflow to move the assets created in `scratch` to `project` and register them.
- Files or directories already existing on S3 cannot be registered, unless they are copied or moved to a target directory indicated by the service.
  This can be discussed further, in case there are use cases that cannot be resolved in other ways.
- The files can be uploaded and associated only to existing entities and projects. If this limitation is too strong, it should be decided:
  - how to organize the files not associated to any entity
  - what to do with any orphaned file that has been uploaded but not associated
- When uploading a file (not a directory) we may consider the magic number to determine the type, instead of relying on the filename extension or the content-type provided by the user. However:
  - this requires additional steps in case of big files uploaded directly to S3, to retrieve the first bytes of the file
  - we cannot control the content of directories, that is completely arbitrary.

### Asset retrieval

- In case of files, the assets can be retrieved through GET requests to the API, that will return a redirect to a presigned url pointing directly to the S3 service.
- In case of directories, it's still possible to retrieve the directory path via the API, and access the content by mounting S3 if the client has the needed privileges.

### Asset update

- To be decided: We may want or not to allow the user to overwrite the content of a file via API.
- We may want to impose some restrictions on when this is possible.
- A similar behaviour could be obtained with deletion + creation of a new asset with the same path.

### Asset deletion

- We may want to allow the user to delete a file via API.
- We may want to impose some restrictions on when this is possible.
- We can keep the record on the database, with a DELETED status.
- However, we need to delete the file from S3, or it will still appear when S3 is mounted.
- Note that it's possible to use versioning-enabled buckets on S3, so that a file deleted can still be recovered until the marker is deleted as well:
https://docs.aws.amazon.com/AmazonS3/latest/userguide/DeletingObjectVersions.html

## API endpoints

```
GET    /{entity_type}/{entity_id}/assets  # Get Entity Assets
POST   /{entity_type}/{entity_id}/assets  # Upload Entity Asset
GET    /{entity_type}/{entity_id}/assets/{asset_id}  # Get Entity Asset
DELETE /{entity_type}/{entity_id}/assets/{asset_id}  # Delete Entity Asset
GET    /{entity_type}/{entity_id}/assets/{asset_id}/download  # Download Entity Asset
POST   /{entity_route}/{entity_id}/assets/directory/upload # Upload Directory
GET    /{entity_route}/{entity_id}/assets/{asset_id}/list  # List Contents of Directory
POST   /{entity_type}/{entity_id}/assets/upload/initiate  # Initiate Entity Asset Upload
POST   /{entity_type}/{entity_id}/assets/upload/complete  # Complete Entity Asset Upload
```

If we need to consider versions/revisions of entities, we may need to use different endpoints.


## Database schema

Tables:

- `asset`: table of assets
  - `id`: int (PK)  # for internal foreign keys
  - `uuid`: UUID  # for external access, not strictly needed
  - `status`: AssetStatus  # (created, deleted...) 
  - `path`: str  # relative path to the file or directory, useful when downloading the asset
  - `fullpath`: str  # full path to the file or directory in the S3 bucket
  - `bucket_name`: str  # name of the S3 bucket (private or public)
  - `is_directory`: bool
  - `content_type`: str 
  - `size`: int8
  - `meta`: dict  # not used yet. can be useful?
  - `entity_id`: int (FK)  # the same asset cannot be shared across multiple entities


## File organization on S3

How to organize the files on S3?

- How many buckets?
    - One bucket for private and one for public
    - or a single bucket
- Possible path templates (for private assets):
  - `project/{proj_id}/{entity_type}/{entity_id}/{relative_file_path}`
    - allows to organize multiple files under the same common parent directory, so that the structure is exposed correctly when mounting S3.
    - the files can be uploaded only after the entity has been created, because the entity_id is needed.
    - we use the basename of the uploaded file or directory under entity_id. Each uploaded item must therefore have a unique name within the entity namespace.
  - `project/{proj_id}/{asset_id}/{relative_file_path}`
    - the files don't share a common parent directory, so they cannot be accessed using subdfolders when mounting S3.
    - the files can be uploaded even before the entity has been created
    - if the files are uploaded and the entity is not created, we can have files not associated with any entity
  - `project/{proj_id}/{asset_id}`
    - similar to the previous case, but the filename can be retrieved only from the db
    - not working well when mounting S3, because the file names are missing
- To be decided: How to move files from private to public?
  - S3 doesn't allow symlinks
  - S3 doesn't allow moving
  - S3 allows copy and delete
  - If we delete the old files, we can break linked entities (for example, an analysis pointing to a simulation)
  - Should we duplicate data?
  - Should we duplicate entities?


## Audit

- We may want to keep tracks of who changed what and when.
- We may want a general solution not specific to assets.
