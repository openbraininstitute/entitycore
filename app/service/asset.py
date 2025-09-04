import uuid
from http import HTTPStatus
from pathlib import Path
from typing import cast

from fastapi import HTTPException
from pydantic.networks import AnyUrl
from types_boto3_s3 import S3Client

from app.config import StorageUnion, storages
from app.db.types import AssetLabel, AssetStatus, ContentType, EntityType, StorageType
from app.errors import ApiError, ApiErrorCode, ensure_result, ensure_uniqueness, ensure_valid_schema
from app.queries.common import get_or_create_user_agent
from app.repository.group import RepositoryGroup
from app.schemas.asset import (
    AssetCreate,
    AssetRead,
    DetailedFileList,
    DirectoryUpload,
)
from app.schemas.auth import UserContext, UserContextWithProjectId
from app.service import entity as entity_service
from app.utils.s3 import (
    StorageClientFactory,
    build_s3_path,
    delete_from_s3,
    generate_presigned_url,
    list_directory_with_details,
    sanitize_directory_traversal,
)


def get_entity_assets(
    repos: RepositoryGroup,
    user_context: UserContext,
    entity_type: EntityType,
    entity_id: uuid.UUID,
) -> list[AssetRead]:
    """Return the list of assets associated with a specific entity."""
    _ = entity_service.get_readable_entity(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    return [
        AssetRead.model_validate(row)
        for row in repos.asset.get_entity_assets(entity_type=entity_type, entity_id=entity_id)
    ]


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
) -> AssetRead:
    """Create an asset for an entity."""
    entity = entity_service.get_writable_entity(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    full_path = full_path or build_s3_path(
        vlab_id=user_context.virtual_lab_id,
        proj_id=user_context.project_id,
        entity_type=entity_type,
        entity_id=entity_id,
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
            entity_type=entity_type,
            storage_type=storage_type,
            created_by_id=db_agent.id,
            updated_by_id=db_agent.id,
        )
    with ensure_uniqueness(
        f"Asset with path {asset_create.path!r} and "
        f"full_path {asset_create.full_path!r} already exists",
        error_code=ApiErrorCode.ASSET_DUPLICATED,
    ):
        asset_db = repos.asset.create_entity_asset(
            entity_id=entity_id,
            asset=asset_create,
        )
    return AssetRead.model_validate(asset_db)


def delete_entity_asset(
    repos: RepositoryGroup,
    user_context: UserContextWithProjectId,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
    *,
    hard_delete: bool = False,
) -> AssetRead:
    """Delete or mark an entity asset as deleted."""
    _ = entity_service.get_writable_entity(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    with ensure_result(f"Asset {asset_id} not found", error_code=ApiErrorCode.ASSET_NOT_FOUND):
        asset = delete_asset(repos, entity_type, entity_id, asset_id, hard_delete=hard_delete)
    return AssetRead.model_validate(asset)


def delete_asset(
    repos: RepositoryGroup,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
    *,
    hard_delete: bool = False,
) -> AssetRead:
    """Delete an asset."""
    with ensure_result(f"Asset {asset_id} not found", error_code=ApiErrorCode.ASSET_NOT_FOUND):
        if hard_delete:
            asset = repos.asset.delete_entity_asset(
                entity_type=entity_type,
                entity_id=entity_id,
                asset_id=asset_id,
            )
        else:
            asset = repos.asset.update_entity_asset_status(
                entity_type=entity_type,
                entity_id=entity_id,
                asset_id=asset_id,
                asset_status=AssetStatus.DELETED,
            )
    return AssetRead.model_validate(asset)


def delete_asset_storage_object(asset: AssetRead, storage_client_factory: StorageClientFactory):
    """Delete asset storage object."""
    # TODO: Handle directories?
    storage = storages[asset.storage_type]
    # delete the file from S3 only if not using an open data storage
    if not storage.is_open:
        s3_client = storage_client_factory(storage)
        if not delete_from_s3(s3_client, bucket_name=storage.bucket, s3_key=asset.full_path):
            raise HTTPException(status_code=500, detail="Failed to delete object")


def entity_asset_upload_directory(
    repos: RepositoryGroup,
    user_context: UserContextWithProjectId,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    s3_client: S3Client,
    storage: StorageUnion,
    files: DirectoryUpload,
) -> tuple[AssetRead, dict[Path, AnyUrl]]:
    if not files.files:
        raise ApiError(
            message="`files` is empty",
            error_code=ApiErrorCode.ASSET_MISSING_PATH,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    paths = [sanitize_directory_traversal(f) for f in files.files]

    if len(set(paths)) != len(paths):
        raise ApiError(
            message="Duplicate file paths",
            error_code=ApiErrorCode.ASSET_INVALID_PATH,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    entity = entity_service.get_writable_entity(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
    )

    full_path = build_s3_path(
        vlab_id=user_context.virtual_lab_id,
        proj_id=user_context.project_id,
        entity_type=entity_type,
        entity_id=entity_id,
        filename=files.directory_name,
        is_public=entity.authorized_public,
    )

    db_agent = get_or_create_user_agent(repos.db, user_profile=user_context.profile)

    with ensure_valid_schema(
        "Asset schema is invalid", error_code=ApiErrorCode.ASSET_INVALID_SCHEMA
    ):
        asset_create = AssetCreate(
            path=str(files.directory_name),
            full_path=full_path,
            is_directory=True,
            content_type=ContentType.directory,
            size=-1,
            sha256_digest=None,
            meta=files.meta or {},
            label=files.label,
            entity_type=entity_type,
            storage_type=storage.type,
            created_by_id=db_agent.id,
            updated_by_id=db_agent.id,
        )

    with ensure_uniqueness(
        f"Asset with path {asset_create.path!r} and "
        f"full_path {asset_create.full_path!r} already exists",
        error_code=ApiErrorCode.ASSET_DUPLICATED,
    ):
        asset_db = repos.asset.create_entity_asset(
            entity_id=entity_id,
            asset=asset_create,
        )

    urls: dict[Path, AnyUrl] = {}
    for f in paths:
        full_path = build_s3_path(
            vlab_id=user_context.virtual_lab_id,
            proj_id=user_context.project_id,
            entity_type=entity_type,
            entity_id=entity_id,
            filename=files.directory_name / f,
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
                message=f"Could not create presigned url for {f}",
                error_code=ApiErrorCode.S3_CANNOT_CREATE_PRESIGNED_URL,
                http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            )

        urls[f] = AnyUrl(url)

    return AssetRead.model_validate(asset_db), urls


def list_directory(
    repos: RepositoryGroup,
    user_context: UserContextWithProjectId,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
    storage_client_factory: StorageClientFactory,
) -> DetailedFileList:
    asset = get_entity_asset(
        repos,
        user_context=cast("UserContext", user_context),
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
