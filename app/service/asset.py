import base64
import mimetypes
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from http import HTTPStatus
from pathlib import Path
from typing import cast

import boto3
import sqlalchemy as sa
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, UploadFile
from pydantic import TypeAdapter, ValidationError
from pydantic.networks import AnyUrl
from starlette.responses import RedirectResponse
from types_boto3_s3 import S3Client

from app.config import StorageUnion, settings, storages
from app.db.events import StorageUndo, undo_storage_write_unless_committed
from app.db.model import Asset, Entity, Identifiable
from app.db.types import AssetLabel, AssetStatus, ContentType, EntityType, StorageType
from app.db.utils import allowed_asset_labels_for
from app.dependencies.common import PaginationQuery
from app.dependencies.filter import FilterDep
from app.errors import ApiError, ApiErrorCode, ensure_result, ensure_uniqueness, ensure_valid_schema
from app.filters.asset import AssetFilter
from app.logger import L
from app.queries import crud
from app.queries.common import get_or_create_user, router_read_many
from app.queries.utils import is_user_authorized_for_deletion
from app.repository.group import RepositoryGroup
from app.schemas.asset import (
    AssetCreate,
    AssetRead,
    AssetReadWithUploadMeta,
    AssetRegister,
    DetailedFileList,
    DirectoryAddFile,
    DirectoryAddFilesRequest,
    DirectoryAddFilesResponse,
    DirectoryUploadRequest,
    MultipartDirectoryFileRequest,
    MultipartDirectoryUploadRequest,
    MultipartDirectoryUploadResponse,
    MultipartUploadInitiateRequest,
    Sha256Digest,
    UploadMeta,
    validate_asset_label,
    validate_relative_path,
)
from app.schemas.auth import UserContext, UserProfile
from app.schemas.types import ListResponse
from app.service import entity as entity_service
from app.service.asset_helpers import (
    build_asset_read_with_upload_meta,
    complete_asset_s3,
    complete_empty_asset_s3,
    generate_upload_presigned_urls,
    initiate_multipart_upload,
)
from app.types import EntityRoute
from app.utils.files import get_content_type
from app.utils.routers import entity_route_to_type
from app.utils.s3 import (
    StorageClientFactory,
    _apply_presigned_url_netloc,
    build_s3_path,
    check_object,
    generate_presigned_url,
    list_directory_with_details,
    put_object_checked,
    upload_to_s3_single_part,
    validate_filename,
    validate_filesize,
    validate_multipart_filesize,
)
from app.utils.virtual_lab import resolve_virtual_lab_id

# 15 min, not the usual 6 h, so a late upload can't land in a directory deleted or moved since
# S3 checks it when the upload starts, so a slow upload still finishes
ADD_FILES_URL_EXPIRATION = 15 * 60

# checks an If-Match with the same Sha256Digest rule the API uses
_SHA256_DIGEST = TypeAdapter(Sha256Digest)
# one SigV4 client per (endpoint, region)
_SIGV4_CLIENTS: dict[tuple[str, str], S3Client] = {}


def get_entity_assets(
    repos: RepositoryGroup,
    user_context: UserContext,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    pagination_request: PaginationQuery,
    filter_model: FilterDep[AssetFilter],
) -> ListResponse[AssetRead]:
    """Return the list of assets associated with a specific entity."""
    db_model_class = Asset
    entity_type = entity_route_to_type(entity_route)
    _ = entity_service.get_readable_entity(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    apply_filter_query_operations = lambda q: q.join(Entity, Entity.id == Asset.entity_id).where(
        Asset.entity_id == entity_id,
        Asset.parent_id.is_(None),
        Entity.type == entity_type.name,
    )
    name_to_facet_query_params = join_specs = None
    return router_read_many(
        db=repos.db,
        db_model_class=db_model_class,
        authorized_project_id=user_context.project_id,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=None,
        apply_filter_query_operations=apply_filter_query_operations,
        apply_data_query_operations=None,
        pagination_request=pagination_request,
        response_schema_class=AssetRead,
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=filter_model,
        join_specs=join_specs,
    )


def get_entity_asset(
    repos: RepositoryGroup,
    user_context: UserContext,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> AssetRead:
    """Return an asset associated with a specific entity."""
    _ = entity_service.get_readable_entity(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    with ensure_result(f"Asset {asset_id} not found", error_code=ApiErrorCode.ASSET_NOT_FOUND):
        asset = repos.asset.get_entity_asset(
            entity_type=entity_type, entity_id=entity_id, asset_id=asset_id
        )
    return AssetRead.model_validate(asset)


def get_writable_entity_db_asset(
    repos: RepositoryGroup,
    user_context: UserContext,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> Asset:
    """Return an asset associated with a specific entity."""
    _ = entity_service.get_writable_entity_by_context(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    with ensure_result(f"Asset {asset_id} not found", error_code=ApiErrorCode.ASSET_NOT_FOUND):
        asset = repos.asset.get_entity_asset(
            entity_type=entity_type, entity_id=entity_id, asset_id=asset_id
        )

    return asset


def create_entity_asset_unverified(  # ruff:ignore[too-many-arguments]
    repos: RepositoryGroup,
    *,
    entity: Entity,
    user_profile: UserProfile,
    virtual_lab_id: uuid.UUID,
    filename: str,
    content_type: ContentType,
    size: int,
    sha256_digest: str | None,
    meta: dict | None,
    label: AssetLabel,
    is_directory: bool,
    storage_type: StorageType,
    full_path: str | None = None,
    status: AssetStatus = AssetStatus.CREATED,
    parent_id: uuid.UUID | None = None,
) -> Asset:
    """Create an asset for the specified entity object, that is assumed to be writable.

    Args:
        repos: Repository group for database access.
        entity: Entity object for full_path construction. The caller is responsible to verify
            that the user has the required write permissions to that entity.
        filename: Name of the file to be stored in the asset path.
        content_type: Content type of the asset.
        size: Size of the asset in bytes.
        sha256_digest: Optional sha256 digest of the asset content.
        meta: Optional metadata dictionary to store additional information about the asset.
        label: Label for categorizing the asset.
        is_directory: Whether the asset represents a directory (True) or a file (False).
        storage_type: The storage type where the asset will be stored.
        full_path: Optional full path for the asset in storage. If not provided, it will be
            automatically constructed based on conventions.
        status: Initial status of the asset. Defaults to CREATED.
        parent_id: Optional ID of the parent asset if this asset is a sub-path of a directory asset.
        user_profile: The user's profile
        virtual_lab_id: The id of the virtual lab to construct the s3 path from
    """
    full_path = full_path or build_s3_path(
        vlab_id=virtual_lab_id,
        proj_id=entity.authorized_project_id,
        entity_type=entity.type,
        entity_id=entity.id,
        filename=filename,
        is_public=entity.authorized_public,
    )

    db_user = get_or_create_user(repos.db, user_profile=user_profile)

    with ensure_valid_schema(
        "Asset schema is invalid", error_code=ApiErrorCode.ASSET_INVALID_SCHEMA
    ):
        asset_create = AssetCreate(
            path=filename,
            full_path=full_path,
            is_directory=is_directory,
            content_type=content_type,
            size=size,
            sha256_digest=sha256_digest,
            meta=meta or {},
            label=label,
            entity_type=entity.type,
            storage_type=storage_type,
            parent_id=parent_id,
            created_by_id=db_user.id,
            updated_by_id=db_user.id,
        )
        validate_asset_label(
            asset_create,
            allowed_asset_labels_for(entity),
        )
    with ensure_uniqueness(
        f"Asset with path {asset_create.path!r} and "
        f"full_path {asset_create.full_path!r} already exists",
        error_code=ApiErrorCode.ASSET_DUPLICATED,
    ):
        return repos.asset.create_entity_asset(
            entity_id=entity.id,
            asset=asset_create,
            status=status,
        )


def upload_and_create_entity_asset(
    repos: RepositoryGroup,
    *,
    entity: Entity,
    user_profile: UserProfile,
    virtual_lab_id: uuid.UUID,
    storage_client_factory: StorageClientFactory,
    file: UploadFile,
    label: AssetLabel,
    meta: dict | None,
) -> AssetRead:
    """Upload a small file to S3 and create its asset row.

    Shared by the standard and admin upload flows. The caller is responsible for
    resolving ``entity`` and ``virtual_lab_id`` (including any authorization checks).

    The asset row is created first, then the file is uploaded to S3 (which computes its
    SHA256 digest in a single request) and the digest is set on the row. The upload is
    the last step, so if it fails the surrounding request transaction is rolled back and
    no orphan row or object is left behind.

    Args:
        repos: Repository group for database access.
        entity: The writable entity the asset is associated with.
        user_profile: The uploader's profile.
        virtual_lab_id: The virtual lab used to construct the S3 path.
        storage_client_factory: Factory returning an S3 client for a storage.
        file: The uploaded file.
        label: Label categorizing the asset.
        meta: Optional metadata to store with the asset.
    """
    storage = storages[StorageType.aws_s3_internal]
    s3_client = storage_client_factory(storage)
    content_type = validate_uploadfile_for_small_entity_post(file)
    asset_db = create_entity_asset_unverified(
        repos,
        entity=entity,
        filename=cast("str", file.filename),
        content_type=content_type,
        size=file.size or 0,
        sha256_digest=None,
        meta=meta,
        label=label,
        is_directory=False,
        storage_type=storage.type,
        user_profile=user_profile,
        virtual_lab_id=virtual_lab_id,
    )
    sha256_digest = upload_to_s3_single_part(
        s3_client,
        file_obj=file.file,
        bucket_name=storage.bucket,
        s3_key=asset_db.full_path,
        content_type=content_type,
    )
    if sha256_digest is None:
        raise HTTPException(status_code=500, detail="Failed to upload object")
    asset_db.sha256_digest = bytes.fromhex(sha256_digest)
    return AssetRead.model_validate(asset_db)


def validate_uploadfile_for_small_entity_post(file: UploadFile) -> ContentType:
    """Validate size/name/content type for small file uploads."""
    if file.size and not validate_filesize(file.size):
        msg = f"File not allowed because bigger than {settings.API_ASSET_POST_MAX_SIZE}"
        raise ApiError(
            message=msg,
            error_code=ApiErrorCode.ASSET_INVALID_FILE,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    if not file.filename or not validate_filename(file.filename):
        msg = f"Invalid file name {file.filename!r}"
        raise ApiError(
            message=msg,
            error_code=ApiErrorCode.ASSET_INVALID_PATH,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    try:
        return get_content_type(file)
    except ValueError as e:
        msg = (
            f"Invalid content type for file {file.filename}. "
            f"Supported content types: {sorted(c.value for c in ContentType)}.\n"
            f"Exception: {e}"
        )
        raise ApiError(
            message=msg,
            error_code=ApiErrorCode.ASSET_INVALID_CONTENT_TYPE,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        ) from None


def upload_entity_asset(
    repos: RepositoryGroup,
    *,
    user_context: UserContext,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    storage_client_factory: StorageClientFactory,
    file: UploadFile,
    label: AssetLabel,
    meta: dict | None = None,
) -> AssetRead:
    """Upload a small file asset for standard project-authorized users.

    The entity's writability is verified before the file is uploaded and its asset row
    is created (see ``upload_and_create_entity_asset``).
    """
    entity = entity_service.get_writable_entity_by_context(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    virtual_lab_id = resolve_virtual_lab_id(user_context, entity.authorized_project_id)
    return upload_and_create_entity_asset(
        repos,
        entity=entity,
        user_profile=user_context.profile,
        virtual_lab_id=virtual_lab_id,
        storage_client_factory=storage_client_factory,
        file=file,
        label=label,
        meta=meta,
    )


def replace_entity_asset(
    repos: RepositoryGroup,
    *,
    user_context: UserContext,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
    storage_client_factory: StorageClientFactory,
    file: UploadFile,
    if_match: str | None,
) -> AssetRead:
    """Replace the content of a small file asset. Its id, path and label stay the same.

    Only for labels marked ``is_replaceable``. The object is overwritten at the same S3 key, so
    a reader gets either the old or the new content, never half of each. A versioned bucket
    keeps the old content as a previous version.

    Optimistic concurrency: ``if_match`` is the sha256 the caller last read. We only replace
    while that's still the current content, so someone working from an older version gets
    HTTP 412 instead of quietly overwriting a newer edit.
    """
    entity = entity_service.get_writable_entity_by_context(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    # A public entity is published, so overwriting it needs the same rights as deleting it.
    if entity.authorized_public and not is_user_authorized_for_deletion(
        repos.db, user_context, entity
    ):
        raise ApiError(
            message="User is not authorized to replace the content of a public entity.",
            error_code=ApiErrorCode.ENTITY_FORBIDDEN,
            http_status_code=HTTPStatus.FORBIDDEN,
        )
    return replace_entity_asset_unverified(
        repos,
        entity=entity,
        entity_type=entity_type,
        user_profile=user_context.profile,
        asset_id=asset_id,
        storage_client_factory=storage_client_factory,
        file=file,
        if_match=if_match,
    )


def replace_entity_asset_unverified(
    repos: RepositoryGroup,
    *,
    entity: Entity,
    entity_type: EntityType,
    user_profile: UserProfile,
    asset_id: uuid.UUID,
    storage_client_factory: StorageClientFactory,
    file: UploadFile,
    if_match: str | None,
) -> AssetRead:
    """Replace the content of a file asset of ``entity``. Caller rights are already checked.

    Same rules as ``replace_entity_asset``, except for who may write: the user route checks
    the project and the public flag first, the admin route checks the admin role.

    The S3 write can't join the database transaction, so we compensate: the bucket keeps the
    old version, and if the transaction doesn't commit we delete the version we just wrote,
    which makes the old one current again (``app.db.events.undo_storage_write_unless_committed``).
    Readers may briefly see the new content; the row and the object match again once the
    transaction ends. Replacing also bumps the entity's ``update_date``, since its content
    changed.
    """
    with ensure_result(f"Asset {asset_id} not found", error_code=ApiErrorCode.ASSET_NOT_FOUND):
        asset = repos.asset.get_entity_asset(
            entity_type=entity_type, entity_id=entity.id, asset_id=asset_id
        )
        # Lock the row until commit and read it again under the lock. Two replaces of the same
        # asset then run one after the other, and each compares against what the other left.
        # An asset deleted since the first read gives a 404, not a 500.
        repos.db.execute(
            sa.select(Asset)
            .where(Asset.id == asset.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        ).scalar_one()

    requirements = (allowed_asset_labels_for(entity) or {}).get(asset.label, [])
    if (
        asset.is_directory
        or asset.storage_type != StorageType.aws_s3_internal
        or not any(r.is_replaceable for r in requirements)
    ):
        raise ApiError(
            message=f"Assets with label {asset.label} cannot be replaced",
            error_code=ApiErrorCode.ASSET_NOT_REPLACEABLE,
            http_status_code=HTTPStatus.CONFLICT,
        )
    if asset.status != AssetStatus.CREATED:
        raise ApiError(
            message="Cannot replace an uploading asset, because it is incomplete.",
            error_code=ApiErrorCode.ASSET_UPLOAD_INCOMPLETE,
            http_status_code=HTTPStatus.CONFLICT,
        )
    content_type = validate_uploadfile_for_small_entity_post(file)
    if content_type != asset.content_type:
        raise ApiError(
            message=f"Content type {content_type} differs from the asset's {asset.content_type}",
            error_code=ApiErrorCode.ASSET_INVALID_CONTENT_TYPE,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    # Checked after the asset's own rules, so a never-replaceable asset gets 409, not 428.
    expected = _expected_sha256(if_match)
    current = asset.sha256_digest.hex() if asset.sha256_digest else None
    if current != expected:
        raise ApiError(
            message="The asset changed since you read it: read it again, then replace it.",
            error_code=ApiErrorCode.ASSET_VERSION_MISMATCH,
            http_status_code=HTTPStatus.PRECONDITION_FAILED,
            details={"sha256_digest": current},
        )

    storage = storages[asset.storage_type]
    put = put_object_checked(
        storage_client_factory(storage),
        file_obj=file.file,
        bucket_name=storage.bucket,
        s3_key=asset.full_path,
        content_type=content_type,
    )
    if put is None:
        raise HTTPException(status_code=500, detail="Failed to upload object")
    if put.version_id is None:
        # limit: a bucket without versioning keeps no old version, so a rollback can't take
        # this write back. Every bucket we run (prod, docker, tests) has versioning on.
        # Upgrade: refuse replaces on such a bucket.
        # TODO: think about an alternative
        L.error("No version for s3 object {}: this write can't be undone", asset.full_path)
    else:
        undo_storage_write_unless_committed(
            repos.db,
            StorageUndo(
                storage_type=asset.storage_type,
                s3_key=asset.full_path,
                version_id=put.version_id,
            ),
        )

    user_id = get_or_create_user(repos.db, user_profile).id
    asset.size = file.size or 0
    asset.sha256_digest = bytes.fromhex(put.sha256_hex)
    _mark_updated(asset, user_id)
    # Its content changed too, so lists sorted or filtered by update_date pick it up.
    _mark_updated(entity, user_id)
    repos.db.flush()
    repos.db.refresh(asset)
    return AssetRead.model_validate(asset)


def _mark_updated(row: Identifiable, user_id: uuid.UUID) -> None:
    """Record that this user changed the row just now, the way an entity update does."""
    row.updated_by_id = user_id
    row.update_date = sa.func.statement_timestamp()


def _sigv4_client(s3_client: S3Client) -> S3Client:
    """Return a SigV4-signing copy of ``s3_client``, made once per endpoint and region.

    The service's clients use botocore's default, which signs presigned URLs with SigV2.
    SigV2 doesn't cover If-None-Match or Content-Length, so S3 wouldn't enforce them. SigV4
    signs every header we give it. The config stays the same. Presigning makes no network
    call, and a client is thread-safe once created.

    SigV4 also signs the host, so we can't swap in ``S3_PRESIGNED_URL_NETLOC`` after signing
    (with SigV2 we can). Instead this client points at that public host from the start, so
    the later rewrite changes nothing. That's safe: this client only presigns, never calls S3.
    """
    endpoint = _apply_presigned_url_netloc(s3_client.meta.endpoint_url)
    key = (endpoint, s3_client.meta.region_name)
    if key not in _SIGV4_CLIENTS:
        _SIGV4_CLIENTS[key] = boto3.session.Session().client(
            "s3",
            region_name=s3_client.meta.region_name,
            endpoint_url=endpoint,
            config=s3_client.meta.config.merge(Config(signature_version="s3v4")),
        )
    return _SIGV4_CLIENTS[key]


def _expected_sha256(if_match: str | None) -> str:
    """Pull the sha256 (lowercase hex) out of an If-Match header: one ETag, quoted or not.

    Weak ETags, lists and ``*`` are refused: replacing bytes needs the exact version.
    """
    if if_match is None:
        raise ApiError(
            message='Send If-Match with the sha256_digest you last read: If-Match: "<sha256>".',
            error_code=ApiErrorCode.INVALID_REQUEST,
            http_status_code=HTTPStatus.PRECONDITION_REQUIRED,
        )
    value = if_match.strip().removeprefix('"').removesuffix('"').lower()
    try:
        return _SHA256_DIGEST.validate_python(value)
    except ValidationError:
        raise ApiError(
            message="If-Match must be one sha256_digest of the asset: 64 hexadecimal characters.",
            error_code=ApiErrorCode.INVALID_REQUEST,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        ) from None


def delete_entity_asset(
    repos: RepositoryGroup,
    user_context: UserContext,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> AssetRead:
    """Delete an asset from the db."""
    entity = crud.get_identifiable_one(
        db=repos.db,
        db_model_class=Entity,
        id_=entity_id,
    )

    if not is_user_authorized_for_deletion(repos.db, user_context, entity):
        raise ApiError(
            message="User is not authorized to access resource.",
            error_code=ApiErrorCode.ENTITY_FORBIDDEN,
            http_status_code=HTTPStatus.FORBIDDEN,
        )

    with ensure_result(f"Asset {asset_id} not found", error_code=ApiErrorCode.ASSET_NOT_FOUND):
        asset = delete_asset_unverified(repos, entity_type, entity_id, asset_id)
    return AssetRead.model_validate(asset)


def delete_asset_unverified(
    repos: RepositoryGroup,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> AssetRead:
    """Delete an asset from the db withouth checking authorization.

    In case of directory asset with children registered in the db, they are deleted on cascade.

    Asset storage object is deleted via `app.db.events`.
    """
    # TODO: Only directories registered with multipart upload have the children in the db, but
    # all cases should be handled. See https://github.com/openbraininstitute/entitycore/issues/256
    with ensure_result(f"Asset {asset_id} not found", error_code=ApiErrorCode.ASSET_NOT_FOUND):
        asset = repos.asset.delete_entity_asset(
            entity_type=entity_type,
            entity_id=entity_id,
            asset_id=asset_id,
        )
    return AssetRead.model_validate(asset)


def entity_asset_directory_upload(
    repos: RepositoryGroup,
    user_context: UserContext,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    s3_client: S3Client,
    storage: StorageUnion,
    files: DirectoryUploadRequest,
) -> tuple[AssetRead, dict[Path, AnyUrl]]:
    entity = entity_service.get_writable_entity_by_context(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    virtual_lab_id = resolve_virtual_lab_id(user_context, entity.authorized_project_id)
    asset_db = create_entity_asset_unverified(
        repos,
        entity=entity,
        filename=str(files.directory_name),
        content_type=ContentType.directory,
        size=-1,
        sha256_digest=None,
        meta=files.meta,
        label=files.label,
        is_directory=True,
        storage_type=storage.type,
        virtual_lab_id=virtual_lab_id,
        user_profile=user_context.profile,
    )

    urls: dict[Path, AnyUrl] = {}
    for path in [Path(f) for f in files.files]:
        full_path = build_s3_path(
            vlab_id=virtual_lab_id,
            proj_id=entity.authorized_project_id,
            entity_type=entity_type,
            entity_id=entity_id,
            filename=files.directory_name / path,
            is_public=entity.authorized_public,
        )
        url = generate_presigned_url(
            s3_client=s3_client,
            operation="put_object",
            bucket_name=storage.bucket,
            s3_key=full_path,
        )
        if url is None:
            raise ApiError(
                message=f"Could not create presigned url for {path}",
                error_code=ApiErrorCode.S3_CANNOT_CREATE_PRESIGNED_URL,
                http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            )

        urls[path] = AnyUrl(url)

    return AssetRead.model_validate(asset_db), urls


def entity_asset_directory_add_files(
    repos: RepositoryGroup,
    user_context: UserContext,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
    storage_client_factory: StorageClientFactory,
    files: DirectoryAddFilesRequest,
) -> DirectoryAddFilesResponse:
    """Give back one upload URL per new file, to add files to an existing directory.

    Existing files are never replaced: a name that's already there gets 409. When a file
    comes with its size and sha256, S3 itself checks the upload: right bytes only, once.
    """
    asset = get_writable_entity_db_asset(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
        asset_id=asset_id,
    )
    if not asset.is_directory:
        raise ApiError(
            message="Asset is not a directory, files cannot be added",
            error_code=ApiErrorCode.ASSET_NOT_A_DIRECTORY,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    # only a finished directory made with `directory/upload` can take new files.
    # Multipart directories keep a row per file (new files would have none), and open
    # storage is public data we can't write to.
    has_children = repos.db.scalar(sa.select(sa.exists().where(Asset.parent_id == asset.id)))
    if (
        has_children
        or asset.status != AssetStatus.CREATED
        or asset.storage_type != StorageType.aws_s3_internal
    ):
        raise ApiError(
            message="Files can be added only to a completed directory uploaded with presigned urls",
            error_code=ApiErrorCode.ASSET_INVALID_PATH,
            http_status_code=HTTPStatus.CONFLICT,
        )

    storage = storages[asset.storage_type]
    s3_client = storage_client_factory(storage)
    keys = {f.path if isinstance(f, DirectoryAddFile) else f: f for f in files.files}
    # check only the asked names (one S3 HEAD each), not the whole directory listing.
    taken = sorted(
        path
        for path in keys
        if check_object(
            s3_client,
            bucket_name=storage.bucket,
            s3_key=str(Path(asset.full_path) / path),
            is_directory=False,
        )["exists"]
    )
    if taken:
        raise ApiError(
            message=f"These files already exist in the directory: {', '.join(taken)}",
            error_code=ApiErrorCode.ASSET_DUPLICATED,
            http_status_code=HTTPStatus.CONFLICT,
            details={"existing": taken},
        )

    # Limit: a bare path gets a URL with no checks, so two uploads to the same new name can
    # both land and the last one wins. Upgrade: drop bare paths once no caller sends them.
    urls: dict[Path, AnyUrl] = {}
    headers: dict[Path, dict[str, str]] = {}
    for path, entry in keys.items():
        params: dict[str, str | int] = {
            "Bucket": storage.bucket,
            "Key": str(Path(asset.full_path) / path),
        }
        if isinstance(entry, DirectoryAddFile):
            # S3 then takes only these bytes, and only once. The client must send these headers.
            checksum = base64.b64encode(bytes.fromhex(entry.sha256_digest)).decode()
            params |= {"IfNoneMatch": "*", "ContentLength": entry.size, "ChecksumSHA256": checksum}
            headers[Path(path)] = {
                "If-None-Match": "*",
                "Content-Length": str(entry.size),
                "x-amz-checksum-sha256": checksum,
            }
        # Only SigV4 signs those headers. The default (SigV2) would ignore them.
        signer = _sigv4_client(s3_client) if isinstance(entry, DirectoryAddFile) else s3_client
        try:
            url = signer.generate_presigned_url(
                "put_object", Params=params, ExpiresIn=ADD_FILES_URL_EXPIRATION
            )
        except (BotoCoreError, ClientError) as e:
            raise ApiError(
                message=f"Could not create presigned url for {path}",
                error_code=ApiErrorCode.S3_CANNOT_CREATE_PRESIGNED_URL,
                http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            ) from e
        # Swap the host like every other presigned URL does (for local docker).
        urls[Path(path)] = AnyUrl(_apply_presigned_url_netloc(url))

    # bump the entity's update date now, once per call: S3 won't tell us when files land.
    # limit: a link that's never used still bumps it.
    _mark_updated(
        repos.db.get_one(Entity, asset.entity_id),
        get_or_create_user(repos.db, user_context.profile).id,
    )
    return DirectoryAddFilesResponse(
        asset=AssetRead.model_validate(asset), files=urls, headers=headers
    )


def register_entity_asset_unverified(
    repos: RepositoryGroup,
    *,
    entity: Entity,
    virtual_lab_id: uuid.UUID,
    user_profile: UserProfile,
    storage_client_factory: StorageClientFactory,
    asset: AssetRegister,
) -> AssetRead:
    """Register an asset already in cloud, without checking authorization."""
    storage = storages[asset.storage_type]
    s3_client = storage_client_factory(storage)
    try:
        check_result = check_object(
            s3_client,
            bucket_name=storage.bucket,
            s3_key=asset.full_path,
            is_directory=asset.is_directory,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to check object") from e
    if not check_result["exists"]:
        raise ApiError(
            message="Object does not exist in S3",
            error_code=ApiErrorCode.ASSET_NOT_FOUND,
            http_status_code=HTTPStatus.CONFLICT,
            details={
                "bucket": storage.bucket,
                "region": storage.region,
                "s3_key": asset.full_path,
            },
        )
    return AssetRead.model_validate(
        create_entity_asset_unverified(
            repos,
            entity=entity,
            filename=asset.path,
            content_type=asset.content_type,
            size=-1,  # considered unknown for already existing assets
            sha256_digest=None,  # considered unknown for already existing assets
            meta=asset.meta,
            label=asset.label,
            is_directory=asset.is_directory,
            storage_type=storage.type,
            full_path=asset.full_path,
            user_profile=user_profile,
            virtual_lab_id=virtual_lab_id,
        )
    )


def multipart_upload_initiate_unverified(
    repos: RepositoryGroup,
    *,
    entity: Entity,
    virtual_lab_id: uuid.UUID,
    user_profile: UserProfile,
    s3_client: S3Client,
    storage: StorageUnion,
    json_model: MultipartUploadInitiateRequest,
) -> AssetReadWithUploadMeta:
    """Initiate a multipart file upload, without checking authorization."""
    if not validate_multipart_filesize(json_model.filesize):
        raise ApiError(
            message=f"File not allowed because bigger than {settings.S3_MULTIPART_UPLOAD_MAX_SIZE}",
            error_code=ApiErrorCode.ASSET_INVALID_FILE,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    if not validate_filename(json_model.filename):
        raise ApiError(
            message=f"Invalid file name {json_model.filename!r}",
            error_code=ApiErrorCode.ASSET_INVALID_PATH,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    try:
        content_type = get_content_type(json_model)
    except ValueError as e:
        raise ApiError(
            message=(
                f"Invalid content type for file {json_model.filename}. "
                f"Supported content types: {sorted(c.value for c in ContentType)}.\n"
                f"Exception: {e}"
            ),
            error_code=ApiErrorCode.ASSET_INVALID_CONTENT_TYPE,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        ) from None
    asset_read = AssetRead.model_validate(
        create_entity_asset_unverified(
            repos,
            entity=entity,
            filename=json_model.filename,
            content_type=content_type,
            size=json_model.filesize,
            sha256_digest=json_model.sha256_digest,
            meta=None,
            label=json_model.label,
            is_directory=False,
            storage_type=storage.type,
            status=AssetStatus.UPLOADING,
            user_profile=user_profile,
            virtual_lab_id=virtual_lab_id,
        )
    )
    return _entity_asset_multipart_upload_initiate(
        repos=repos,
        s3_client=s3_client,
        entity_type=entity.type,
        entity_id=entity.id,
        asset_id=asset_read.id,
        bucket=storage.bucket,
        s3_key=asset_read.full_path,
        filesize=json_model.filesize,
        content_type=content_type,
        preferred_part_count=json_model.preferred_part_count,
    )


def register_entity_asset(
    repos: RepositoryGroup,
    *,
    user_context: UserContext,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    storage_client_factory: StorageClientFactory,
    asset: AssetRegister,
) -> AssetRead:
    """Register an asset already in cloud."""
    entity = entity_service.get_writable_entity_by_context(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    virtual_lab_id = resolve_virtual_lab_id(user_context, entity.authorized_project_id)
    return register_entity_asset_unverified(
        repos,
        entity=entity,
        virtual_lab_id=virtual_lab_id,
        user_profile=user_context.profile,
        storage_client_factory=storage_client_factory,
        asset=asset,
    )


def multipart_upload_initiate(
    repos: RepositoryGroup,
    *,
    user_context: UserContext,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    storage_client_factory: StorageClientFactory,
    json_model: MultipartUploadInitiateRequest,
) -> AssetReadWithUploadMeta:
    """Initiate a multipart file upload."""
    entity = entity_service.get_writable_entity_by_context(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    virtual_lab_id = resolve_virtual_lab_id(user_context, entity.authorized_project_id)
    storage = storages[StorageType.aws_s3_internal]
    s3_client = storage_client_factory(storage)
    return multipart_upload_initiate_unverified(
        repos,
        entity=entity,
        virtual_lab_id=virtual_lab_id,
        user_profile=user_context.profile,
        s3_client=s3_client,
        storage=storage,
        json_model=json_model,
    )


def list_directory_unverified(
    *,
    asset: AssetRead,
    storage_client_factory: StorageClientFactory,
) -> DetailedFileList:
    """Return the list of files in a directory asset, without checking authorization."""
    if not asset.is_directory:
        raise ApiError(
            message="Asset is not a directory, cannot be listed",
            error_code=ApiErrorCode.ASSET_NOT_A_DIRECTORY,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    storage = storages[asset.storage_type]
    s3_client = storage_client_factory(storage)
    ret = list_directory_with_details(
        s3_client,
        bucket_name=storage.bucket,
        prefix=asset.full_path,
    )
    return DetailedFileList.model_validate({"files": ret})


def list_directory(
    repos: RepositoryGroup,
    user_context: UserContext,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
    storage_client_factory: StorageClientFactory,
) -> DetailedFileList:
    asset = get_entity_asset(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
        asset_id=asset_id,
    )
    return list_directory_unverified(asset=asset, storage_client_factory=storage_client_factory)


def _entity_asset_multipart_upload_initiate(
    *,
    repos: RepositoryGroup,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
    s3_client: S3Client,
    s3_key: str,
    bucket: str,
    filesize: int,
    content_type: ContentType,
    preferred_part_count: int,
) -> AssetReadWithUploadMeta:
    """Initiate a multipart upload for an existing entity asset.

    This function prepares and starts a multipart upload to S3 for the specified
    asset and returns the asset metadata along with upload details (e.g., upload ID,
    part size configuration).

    It is intended to be called immediately after the asset record has been
    created in the router. Because of that, it does not perform any additional
    existence or permission checks.
    """
    with ensure_result(f"Asset {asset_id} not found", error_code=ApiErrorCode.ASSET_NOT_FOUND):
        asset = repos.asset.get_entity_asset(
            entity_type=entity_type,
            entity_id=entity_id,
            asset_id=asset_id,
        )

    upload_meta = initiate_multipart_upload(
        s3_client=s3_client,
        s3_key=s3_key,
        bucket=bucket,
        content_type=content_type,
        filesize=filesize,
        preferred_part_count=preferred_part_count,
    )
    asset.status = AssetStatus.UPLOADING
    asset.upload_meta = upload_meta.model_dump()
    repos.db.flush()

    parts = generate_upload_presigned_urls(s3_client=s3_client, asset=asset)
    return build_asset_read_with_upload_meta(asset, parts)


def multipart_upload_complete_unverified(
    repos: RepositoryGroup,
    asset_db: Asset,
    storage_client_factory: StorageClientFactory,
) -> AssetRead:
    """Complete a multipart upload for an asset, without checking authorization."""
    storage = storages[asset_db.storage_type]
    complete_asset_s3(asset=asset_db, storage=storage, s3_client=storage_client_factory(storage))
    asset_db.status = AssetStatus.CREATED
    repos.db.flush()
    return AssetRead.model_validate(asset_db)


def entity_asset_multipart_upload_complete(
    *,
    repos: RepositoryGroup,
    user_context: UserContext,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
    storage_client_factory: StorageClientFactory,
) -> AssetRead:
    """Complete a multipart upload for an existing entity asset."""
    asset_db = get_writable_entity_db_asset(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
        asset_id=asset_id,
    )
    return multipart_upload_complete_unverified(repos, asset_db, storage_client_factory)


def download_entity_asset(
    repos: RepositoryGroup,
    user_context: UserContext,
    storage_client_factory: StorageClientFactory,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
    asset_path: str | None = None,
) -> RedirectResponse:
    """Download an asset associated with a specific entity.

    This endpoint returns a temporary download link (via HTTP redirect) to the
    requested asset file.

    Availability:
    - Only assets with status `CREATED` can be downloaded.
    - If the asset is in `UPLOADING` status, the request will return
      HTTP 409 (Conflict) because the asset is not yet complete.

    Directory assets:
    - If the asset represents a directory, you must provide the `asset_path`
      query parameter specifying the relative path of the file inside the directory.
    - If `asset_path` is missing for a directory asset, the request will fail
      with HTTP 409.
    - If `asset_path` is provided for a non-directory asset, the request will
      fail with HTTP 409.
    """
    asset = get_entity_asset(
        repos,
        user_context=user_context,
        entity_type=entity_route_to_type(entity_route),
        entity_id=entity_id,
        asset_id=asset_id,
    )
    return create_asset_download_redirect(
        asset=asset,
        storage_client_factory=storage_client_factory,
        asset_path=asset_path,
    )


def create_asset_download_redirect(
    *,
    asset: AssetRead,
    storage_client_factory: StorageClientFactory,
    asset_path: str | None = None,
) -> RedirectResponse:
    """Return a redirect response to download an asset from storage."""
    if asset.status == AssetStatus.UPLOADING:
        raise ApiError(
            message="Cannot download an uploading asset, because it is incomplete.",
            error_code=ApiErrorCode.ASSET_UPLOAD_INCOMPLETE,
            http_status_code=HTTPStatus.CONFLICT,
        )
    if asset.is_directory:
        if asset_path is None:
            msg = "Missing required parameter for downloading a directory file: asset_path"
            raise ApiError(
                message=msg,
                error_code=ApiErrorCode.ASSET_MISSING_PATH,
                http_status_code=HTTPStatus.CONFLICT,
            )
        full_path = str(asset.full_path / validate_relative_path(Path(asset_path)))
        # A file inside a directory has no row of its own, so its type comes from its name.
        content_type, _encoding = mimetypes.guess_type(asset_path, strict=False)
    else:
        if asset_path:
            msg = "asset_path is only applicable when asset is a directory"
            raise ApiError(
                message=msg,
                error_code=ApiErrorCode.ASSET_NOT_A_DIRECTORY,
                http_status_code=HTTPStatus.CONFLICT,
            )
        full_path = str(asset.full_path)
        content_type = asset.content_type

    storage = storages[asset.storage_type]
    s3_client = storage_client_factory(storage)

    # The link sets the type, so old files saved without one still download right.
    # S3 only takes that on a SigV4-signed link, and open data links aren't signed.
    if storage.is_open:
        content_type = None
    else:
        s3_client = _sigv4_client(s3_client)
    url = generate_presigned_url(
        s3_client=s3_client,
        operation="get_object",
        bucket_name=storage.bucket,
        s3_key=full_path,
        response_content_type=content_type,
    )
    if not url:
        raise HTTPException(status_code=500, detail="Failed to generate presigned url")
    return RedirectResponse(url=url)


def directory_multipart_upload_initiate_unverified(
    repos: RepositoryGroup,
    entity: Entity,
    virtual_lab_id: uuid.UUID,
    s3_client: S3Client,
    storage: StorageUnion,
    json_model: MultipartDirectoryUploadRequest,
    user_profile: UserProfile,
) -> MultipartDirectoryUploadResponse:
    """Initiate a multipart directory upload without checking authorization.

    Return presigned urls for all parts.
    """
    # create asset to fail early if full path already in progress or registered
    parent = create_entity_asset_unverified(
        repos=repos,
        entity=entity,
        filename=json_model.directory_name,
        content_type=ContentType.directory,
        size=-1,  # no size
        sha256_digest=None,
        meta=json_model.meta,
        label=json_model.label,
        is_directory=True,
        storage_type=storage.type,
        status=AssetStatus.UPLOADING,
        parent_id=None,
        virtual_lab_id=virtual_lab_id,
        user_profile=user_profile,
    )

    # Phase 1: create all asset DB records (sequential)
    file_assets: list[tuple[Asset, MultipartDirectoryFileRequest]] = []
    for initiate_payload in json_model.files:
        try:
            content_type = get_content_type(initiate_payload, verbose=False)
        except ValueError:
            content_type = ContentType.other
        asset_db = create_entity_asset_unverified(
            repos=repos,
            entity=entity,
            filename=str(Path(json_model.directory_name, initiate_payload.filename)),
            content_type=content_type,
            size=initiate_payload.filesize,
            sha256_digest=initiate_payload.sha256_digest,
            meta=None,
            label=initiate_payload.label,
            is_directory=False,
            storage_type=storage.type,
            status=AssetStatus.UPLOADING,
            parent_id=parent.id,
            user_profile=user_profile,
            virtual_lab_id=virtual_lab_id,
        )
        file_assets.append((asset_db, initiate_payload))

    # Phase 2: initiate multipart uploads (in parallel)
    upload_metas: dict[uuid.UUID, UploadMeta] = {}
    if file_assets:
        max_workers = min(settings.S3_MAX_WORKERS, len(file_assets))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    initiate_multipart_upload,
                    s3_client=s3_client,
                    s3_key=str(asset_db.full_path),
                    bucket=storage.bucket,
                    content_type=asset_db.content_type,
                    filesize=initiate_payload.filesize,
                    preferred_part_count=initiate_payload.preferred_part_count,
                ): asset_db.id
                for asset_db, initiate_payload in file_assets
            }
            for future in as_completed(futures):
                upload_metas[futures[future]] = future.result()

    # Phase 3: write upload_meta to DB and generate presigned URLs (sequential)
    result: list[AssetReadWithUploadMeta] = []
    for asset_db, _ in file_assets:
        asset_db.upload_meta = upload_metas[asset_db.id].model_dump()
        parts = generate_upload_presigned_urls(s3_client=s3_client, asset=asset_db)
        result.append(build_asset_read_with_upload_meta(asset_db, parts))

    return MultipartDirectoryUploadResponse(
        asset=AssetRead.model_validate(parent),
        files=result,
    )


def entity_asset_directory_multipart_upload_initiate(
    *,
    repos: RepositoryGroup,
    user_context: UserContext,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    s3_client: S3Client,
    storage: StorageUnion,
    json_model: MultipartDirectoryUploadRequest,
) -> MultipartDirectoryUploadResponse:
    """Initiate a multipart upload for each file in a directory asset.

    Return presigned urls for all parts.
    """
    entity = entity_service.get_writable_entity_by_context(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    virtual_lab_id = resolve_virtual_lab_id(user_context, entity.authorized_project_id)
    return directory_multipart_upload_initiate_unverified(
        repos=repos,
        entity=entity,
        virtual_lab_id=virtual_lab_id,
        s3_client=s3_client,
        storage=storage,
        json_model=json_model,
        user_profile=user_context.profile,
    )


def directory_multipart_upload_complete_unverified(
    repos: RepositoryGroup,
    asset_db: Asset,
    storage_client_factory: StorageClientFactory,
) -> AssetRead:
    """Complete a multipart upload for a directory asset, without checking authorization."""
    if asset_db.status != AssetStatus.UPLOADING:
        raise ApiError(
            message="Directory asset is not uploading. Operation cannot be performed.",
            error_code=ApiErrorCode.ASSET_NOT_UPLOADING,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    storage = storages[asset_db.storage_type]
    s3_client = storage_client_factory(storage)
    pending_children = [child for child in asset_db.children if child.status != AssetStatus.CREATED]
    if pending_children:
        max_workers = min(settings.S3_MAX_WORKERS, len(pending_children))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(
                    complete_asset_s3 if child.size > 0 else complete_empty_asset_s3,
                    asset=child,
                    storage=storage,
                    s3_client=s3_client,
                )
                for child in pending_children
            ]
            for future in as_completed(futures):
                future.result()
        for child in pending_children:
            child.status = AssetStatus.CREATED
    asset_db.status = AssetStatus.CREATED
    repos.db.flush()
    return AssetRead.model_validate(asset_db)


def entity_asset_directory_multipart_upload_complete(
    *,
    repos: RepositoryGroup,
    user_context: UserContext,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
    storage_client_factory: StorageClientFactory,
) -> AssetRead:
    """Complete a multipart upload for an existing directory asset."""
    asset_db = get_writable_entity_db_asset(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
        asset_id=asset_id,
    )
    return directory_multipart_upload_complete_unverified(repos, asset_db, storage_client_factory)
