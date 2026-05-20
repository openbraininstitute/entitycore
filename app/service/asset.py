import uuid
from http import HTTPStatus
from pathlib import Path
from typing import cast

from fastapi import HTTPException, UploadFile
from pydantic.networks import AnyUrl
from starlette.responses import RedirectResponse
from types_boto3_s3 import S3Client

from app.config import StorageUnion, settings, storages
from app.db.model import Asset, Entity
from app.db.types import AssetLabel, AssetStatus, ContentType, EntityType, StorageType
from app.dependencies.common import PaginationQuery
from app.errors import ApiError, ApiErrorCode, ensure_result, ensure_uniqueness, ensure_valid_schema
from app.filters.asset import AssetFilterDep
from app.logger import L
from app.queries import crud
from app.queries.common import get_or_create_user_agent, router_read_many
from app.queries.utils import is_user_authorized_for_deletion
from app.repository.group import RepositoryGroup
from app.routers.types import EntityRoute
from app.schemas.asset import (
    AssetCreate,
    AssetRead,
    AssetReadWithUploadMeta,
    DetailedFileList,
    DirectoryUploadRequest,
    MultipartDirectoryUploadRequest,
    MultipartDirectoryUploadResponse,
    ToUploadPart,
    UploadMeta,
    UploadMetaRead,
    validate_relative_path,
)
from app.schemas.auth import UserContext, UserContextWithProjectId
from app.schemas.types import ListResponse
from app.service import entity as entity_service
from app.utils.files import calculate_sha256_digest, get_content_type
from app.utils.routers import entity_route_to_type
from app.utils.s3 import (
    StorageClientFactory,
    build_s3_path,
    check_object,
    generate_presigned_url,
    list_directory_with_details,
    multipart_compute_upload_plan,
    multipart_upload_complete,
    multipart_upload_create_part_presigned_url,
    multipart_upload_initiate,
    multipart_upload_list_parts,
    upload_to_s3,
    validate_filename,
    validate_filesize,
)


def get_entity_assets(
    repos: RepositoryGroup,
    user_context: UserContext,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    pagination_request: PaginationQuery,
    filter_model: AssetFilterDep,
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
    name_to_facet_query_params = filter_joins = None
    return router_read_many(
        db=repos.db,
        db_model_class=db_model_class,
        authorized_project_id=user_context.project_id,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases={},
        apply_filter_query_operations=apply_filter_query_operations,
        apply_data_query_operations=None,
        pagination_request=pagination_request,
        response_schema_class=AssetRead,
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=filter_model,
        filter_joins=filter_joins,
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
    user_context: UserContextWithProjectId,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> Asset:
    """Return an asset associated with a specific entity."""
    _ = entity_service.get_writable_entity(
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


def create_entity_asset_unverified(  # noqa: PLR0913
    repos: RepositoryGroup,
    *,
    entity: Entity,
    user_context: UserContextWithProjectId,
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
) -> AssetRead:
    """Create an asset for the specified entity object, that is assumed to be writable.

    Args:
        repos: Repository group for database access.
        user_context: User context for authorization.
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
    """
    full_path = full_path or build_s3_path(
        vlab_id=user_context.virtual_lab_id,
        proj_id=user_context.project_id,
        entity_type=entity.type,
        entity_id=entity.id,
        filename=filename,
        is_public=entity.authorized_public,
    )

    db_agent = get_or_create_user_agent(repos.db, user_profile=user_context.profile)

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
            created_by_id=db_agent.id,
            updated_by_id=db_agent.id,
        )
    with ensure_uniqueness(
        f"Asset with path {asset_create.path!r} and "
        f"full_path {asset_create.full_path!r} already exists",
        error_code=ApiErrorCode.ASSET_DUPLICATED,
    ):
        asset_db = repos.asset.create_entity_asset(
            entity_id=entity.id,
            asset=asset_create,
            status=status,
        )
    return AssetRead.model_validate(asset_db)


def create_entity_asset(  # noqa: PLR0913
    repos: RepositoryGroup,
    *,
    user_context: UserContextWithProjectId,
    entity_type: EntityType,
    entity_id: uuid.UUID,
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
) -> AssetRead:
    """Create an asset for the specified entity id and type.

    Args:
        repos: Repository group for database access.
        user_context: User context for authorization.
        entity_type: Type of the entity the asset is associated with.
        entity_id: ID of the entity the asset is associated with.
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
    """
    entity = entity_service.get_writable_entity(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    return create_entity_asset_unverified(
        repos,
        entity=entity,
        user_context=user_context,
        filename=filename,
        content_type=content_type,
        size=size,
        sha256_digest=sha256_digest,
        meta=meta,
        label=label,
        is_directory=is_directory,
        storage_type=storage_type,
        full_path=full_path,
        status=status,
        parent_id=parent_id,
    )


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
    user_context: UserContextWithProjectId,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    storage_client_factory: StorageClientFactory,
    file: UploadFile,
    label: AssetLabel,
    meta: dict | None = None,
) -> AssetRead:
    """Upload a small file asset for standard project-authorized users."""
    storage = storages[StorageType.aws_s3_internal]
    s3_client = storage_client_factory(storage)
    content_type = validate_uploadfile_for_small_entity_post(file)
    sha256_digest = calculate_sha256_digest(file)
    asset_read = create_entity_asset(
        repos=repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
        filename=cast("str", file.filename),
        content_type=content_type,
        size=file.size or 0,
        sha256_digest=sha256_digest,
        meta=meta,
        label=label,
        is_directory=False,
        storage_type=storage.type,
    )
    if not upload_to_s3(
        s3_client,
        file_obj=file.file,
        bucket_name=storage.bucket,
        s3_key=asset_read.full_path,
    ):
        raise HTTPException(status_code=500, detail="Failed to upload object")
    return asset_read


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
    user_context: UserContextWithProjectId,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    s3_client: S3Client,
    storage: StorageUnion,
    files: DirectoryUploadRequest,
) -> tuple[AssetRead, dict[Path, AnyUrl]]:
    entity = entity_service.get_writable_entity(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
    )

    asset_read = create_entity_asset_unverified(
        repos,
        entity=entity,
        user_context=user_context,
        filename=str(files.directory_name),
        content_type=ContentType.directory,
        size=-1,
        sha256_digest=None,
        meta=files.meta,
        label=files.label,
        is_directory=True,
        storage_type=storage.type,
    )

    urls: dict[Path, AnyUrl] = {}
    for path in [Path(f) for f in files.files]:
        full_path = build_s3_path(
            vlab_id=user_context.virtual_lab_id,
            proj_id=user_context.project_id,
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

    return asset_read, urls


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


def entity_asset_multipart_upload_initiate(
    *,
    repos: RepositoryGroup,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
    s3_client: S3Client,
    s3_key: str,
    bucket: str,
    filesize: int,
    content_type: str,
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

    storage = storages[asset.storage_type]

    upload_id = multipart_upload_initiate(
        s3_client=s3_client,
        s3_key=s3_key,
        bucket=bucket,
        content_type=content_type,
    )
    part_size, part_count = multipart_compute_upload_plan(
        filesize=filesize,
        preferred_part_count=preferred_part_count,
    )
    parts = [
        ToUploadPart(
            part_number=part_number,
            url=multipart_upload_create_part_presigned_url(
                s3_client=s3_client,
                bucket=storage.bucket,
                s3_key=asset.full_path,
                upload_id=upload_id,
                part_number=part_number,
            ),
        )
        for part_number in range(1, part_count + 1)
    ]
    asset.status = AssetStatus.UPLOADING
    asset.upload_meta = UploadMeta(
        upload_id=upload_id,
        part_size=part_size,
        part_count=part_count,
    ).model_dump()
    repos.db.flush()

    # The presigned urls are not stored in the db because not needed and potentially too numerous
    # The upload_id is not provided in the response because it is not needed by the client

    base_asset_read = AssetRead.model_validate(asset)
    upload_meta = UploadMetaRead(part_size=part_size, parts=parts)
    return AssetReadWithUploadMeta.model_validate(
        {**base_asset_read.model_dump(), "upload_meta": upload_meta.model_dump()}
    )


def entity_asset_multipart_upload_complete(
    *,
    repos: RepositoryGroup,
    user_context: UserContextWithProjectId,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
    storage: StorageUnion,
    s3_client: S3Client,
) -> AssetRead:
    """Complete a multipart upload for an existing entity asset."""
    asset_db = get_writable_entity_db_asset(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
        asset_id=asset_id,
    )
    upload_meta = UploadMeta.model_validate(asset_db.upload_meta) if asset_db.upload_meta else None

    if asset_db.status != AssetStatus.UPLOADING or upload_meta is None:
        raise ApiError(
            message="Asset is not uploading. Operation cannot be performed.",
            error_code=ApiErrorCode.ASSET_NOT_UPLOADING,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    # parts that have been already uploaded to s3
    uploaded_parts = multipart_upload_list_parts(
        s3_client=s3_client,
        bucket=storage.bucket,
        s3_key=asset_db.full_path,
        upload_id=upload_meta.upload_id,
    )

    # verify that expected and uploaded agree
    uploaded_part_numbers = {p["PartNumber"] for p in uploaded_parts}
    expected_part_numbers = set(range(1, upload_meta.part_count + 1))

    if uploaded_part_numbers != expected_part_numbers:
        raise ApiError(
            message=(
                "Expected parts are not uploaded. "
                f"Expected: {len(expected_part_numbers)}, Actual: {len(uploaded_part_numbers)}"
            ),
            error_code=ApiErrorCode.ASSET_UPLOAD_INCOMPLETE,
            http_status_code=HTTPStatus.CONFLICT,
        )

    upload_size = sum(p["Size"] for p in uploaded_parts)
    upload_expected_size = asset_db.size

    if upload_size != upload_expected_size:
        raise ApiError(
            message=(
                "Total from multipart upload parts sizes does not match expected size. "
                f"Expected: {upload_expected_size}, Actual: {upload_size}"
            ),
            error_code=ApiErrorCode.ASSET_UPLOAD_INCONSISTENT_SIZE,
            http_status_code=HTTPStatus.CONFLICT,
        )

    multipart_upload_complete(
        s3_client=s3_client,
        s3_key=asset_db.full_path,
        upload_id=upload_meta.upload_id,
        bucket=storage.bucket,
        parts=uploaded_parts,
    )

    asset_db.status = AssetStatus.CREATED
    repos.db.flush()
    return AssetRead.model_validate(asset_db)


def entity_asset_empty_upload_initiate(
    *,
    repos: RepositoryGroup,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
    s3_client: S3Client,
) -> AssetReadWithUploadMeta:
    """Initiate a multipart upload for an existing entity asset.

    This function can be used to upload empty files, since it isn't possible with multipart upload.

    The `upload_meta` in the db will contain:
    `{"part_size": 0, "upload_id": "", "part_count": 0}`

    The returned `upload_meta` will contain:
    `{"part_size": 0, "parts": [{"part_number": 0, "url": "<presigned_url>"}]}`

    In this way the client can process the presigned url in the same way as for multipart uploads.
    """
    with ensure_result(f"Asset {asset_id} not found", error_code=ApiErrorCode.ASSET_NOT_FOUND):
        asset = repos.asset.get_entity_asset(
            entity_type=entity_type,
            entity_id=entity_id,
            asset_id=asset_id,
        )

    storage = storages[asset.storage_type]

    upload_id = ""
    asset.status = AssetStatus.UPLOADING
    asset.upload_meta = UploadMeta(
        upload_id=upload_id,
        part_size=0,
        part_count=0,
    ).model_dump()
    repos.db.flush()

    url = generate_presigned_url(
        s3_client=s3_client,
        operation="put_object",
        bucket_name=storage.bucket,
        s3_key=asset.full_path,
    )
    if url is None:
        raise ApiError(
            message=f"Could not create presigned url for {asset.full_path}",
            error_code=ApiErrorCode.S3_CANNOT_CREATE_PRESIGNED_URL,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    parts = [ToUploadPart(part_number=0, url=url)]
    base_asset_read = AssetRead.model_validate(asset)
    upload_meta = UploadMetaRead(part_size=0, parts=parts)
    return AssetReadWithUploadMeta.model_validate(
        {**base_asset_read.model_dump(), "upload_meta": upload_meta.model_dump()}
    )


def entity_asset_empty_upload_complete(
    *,
    repos: RepositoryGroup,
    user_context: UserContextWithProjectId,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
    storage: StorageUnion,
    s3_client: S3Client,
) -> AssetRead:
    """Complete a multipart upload for an existing entity asset."""
    asset_db = get_writable_entity_db_asset(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
        asset_id=asset_id,
    )
    upload_meta = UploadMeta.model_validate(asset_db.upload_meta) if asset_db.upload_meta else None

    if asset_db.status != AssetStatus.UPLOADING or upload_meta is None:
        raise ApiError(
            message="Asset is not uploading. Operation cannot be performed.",
            error_code=ApiErrorCode.ASSET_NOT_UPLOADING,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    # check that the file exists and is empty
    try:
        check_result = check_object(
            s3_client,
            bucket_name=storage.bucket,
            s3_key=asset_db.full_path,
            is_directory=False,
        )
    except Exception as e:
        raise ApiError(
            message="Failed to check object.",
            error_code=ApiErrorCode.GENERIC_ERROR,
            http_status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        ) from e

    if check_result["exists"] is False:
        raise ApiError(
            message="Uploaded empty file not found.",
            error_code=ApiErrorCode.ASSET_UPLOAD_INCOMPLETE,
            http_status_code=HTTPStatus.CONFLICT,
        )
    if check_result["size"] != 0:
        raise ApiError(
            message=(
                "Uploaded empty file does not match expected size. "
                f"Expected: 0, Actual: {check_result['size']}"
            ),
            error_code=ApiErrorCode.ASSET_UPLOAD_INCONSISTENT_SIZE,
            http_status_code=HTTPStatus.CONFLICT,
        )

    asset_db.status = AssetStatus.CREATED
    repos.db.flush()
    return AssetRead.model_validate(asset_db)


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
    else:
        if asset_path:
            msg = "asset_path is only applicable when asset is a directory"
            raise ApiError(
                message=msg,
                error_code=ApiErrorCode.ASSET_NOT_A_DIRECTORY,
                http_status_code=HTTPStatus.CONFLICT,
            )
        full_path = str(asset.full_path)

    storage = storages[asset.storage_type]
    s3_client = storage_client_factory(storage)

    url = generate_presigned_url(
        s3_client=s3_client,
        operation="get_object",
        bucket_name=storage.bucket,
        s3_key=full_path,
    )
    if not url:
        raise HTTPException(status_code=500, detail="Failed to generate presigned url")
    return RedirectResponse(url=url)


def entity_asset_directory_multipart_upload_initiate(
    *,
    repos: RepositoryGroup,
    user_context: UserContextWithProjectId,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    s3_client: S3Client,
    storage: StorageUnion,
    json_model: MultipartDirectoryUploadRequest,
) -> MultipartDirectoryUploadResponse:
    """Initiate a multipart upload for each file in a directory asset.

    Return presigned urls for all parts.
    """
    entity = entity_service.get_writable_entity(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    # create asset to fail early if full path already in progress or registered
    parent = create_entity_asset_unverified(
        repos=repos,
        entity=entity,
        user_context=user_context,
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
    )
    asset_read_with_upload_meta_list: list[AssetReadWithUploadMeta] = []
    for initiate_payload in json_model.files:
        try:
            content_type = get_content_type(initiate_payload, verbose=False)
        except ValueError:
            # fallback to generic content-type, as there aren't restrictions for directory content
            content_type = ContentType.other
        # create the asset entry in the db for each file
        asset_read = create_entity_asset_unverified(
            repos=repos,
            user_context=user_context,
            entity=entity,
            filename=str(Path(json_model.directory_name, initiate_payload.filename)),
            content_type=content_type,
            size=initiate_payload.filesize,
            sha256_digest=initiate_payload.sha256_digest,
            meta=None,
            label=initiate_payload.label,  # same as json_model.label
            is_directory=False,
            storage_type=storage.type,
            status=AssetStatus.UPLOADING,
            parent_id=parent.id,
        )
        if initiate_payload.filesize > 0:
            # create presigned urls using the part count hint and filesize
            # asset schemas is updated with the upload metadata
            # Note: User already authorized when creating the asset
            asset_read_with_upload_meta = entity_asset_multipart_upload_initiate(
                repos=repos,
                s3_client=s3_client,
                entity_type=entity_type,
                entity_id=entity_id,
                asset_id=asset_read.id,
                bucket=storage.bucket,
                s3_key=asset_read.full_path,
                filesize=initiate_payload.filesize,
                content_type=content_type,
                preferred_part_count=initiate_payload.preferred_part_count,
            )
        else:
            # create a simple presigned url for an empty file that cannot be uploaded with multipart
            asset_read_with_upload_meta = entity_asset_empty_upload_initiate(
                repos=repos,
                s3_client=s3_client,
                entity_type=entity_type,
                entity_id=entity_id,
                asset_id=asset_read.id,
            )
        asset_read_with_upload_meta_list.append(asset_read_with_upload_meta)
    return MultipartDirectoryUploadResponse(
        asset=parent,
        files=asset_read_with_upload_meta_list,
    )


def entity_asset_directory_multipart_upload_complete(
    *,
    repos: RepositoryGroup,
    user_context: UserContextWithProjectId,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
    storage: StorageUnion,
    s3_client: S3Client,
) -> AssetRead:
    """Complete a multipart upload for an existing directory asset."""
    asset_db = get_writable_entity_db_asset(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
        asset_id=asset_id,
    )
    if asset_db.status != AssetStatus.UPLOADING:
        raise ApiError(
            message="Directory asset is not uploading. Operation cannot be performed.",
            error_code=ApiErrorCode.ASSET_NOT_UPLOADING,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    for child in asset_db.children:
        if child.status == AssetStatus.CREATED:
            L.debug("Child asset upload already completed, skipping completion for id {}", child.id)
            continue
        if child.size > 0:
            entity_asset_multipart_upload_complete(
                repos=repos,
                user_context=user_context,
                entity_type=entity_type,
                entity_id=entity_id,
                asset_id=child.id,
                storage=storage,
                s3_client=s3_client,
            )
            L.debug("Child asset upload completed for id {}", child.id)
        else:
            entity_asset_empty_upload_complete(
                repos=repos,
                user_context=user_context,
                entity_type=entity_type,
                entity_id=entity_id,
                asset_id=child.id,
                storage=storage,
                s3_client=s3_client,
            )
            L.debug("Empty child asset upload verified for id {}", child.id)
    asset_db.status = AssetStatus.CREATED
    repos.db.flush()
    return AssetRead.model_validate(asset_db)
