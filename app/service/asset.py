import os
import uuid
from pathlib import Path

from pydantic.networks import AnyUrl

from app.config import settings
from app.db.types import AssetLabel, AssetStatus, EntityType
from app.dependencies.s3 import S3ClientDep
from app.errors import ApiErrorCode, ensure_result, ensure_uniqueness, ensure_valid_schema
from app.queries.common import get_or_create_user_agent
from app.repository.group import RepositoryGroup
from app.schemas.asset import AssetCreate, AssetRead, DetailedFileList, FileList
from app.schemas.auth import UserContext, UserContextWithProjectId
from app.service import entity as entity_service
from app.utils.s3 import build_s3_path, generate_presigned_url, list_directory_with_details
from app.utils.uuid import create_uuid


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


def create_entity_asset(
    repos: RepositoryGroup,
    user_context: UserContextWithProjectId,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    filename: str,
    content_type: str,
    size: int,
    sha256_digest: str | None,
    meta: dict | None,
    label: AssetLabel | None,
) -> AssetRead:
    """Create an asset for an entity."""
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
            is_directory=False,
            content_type=content_type,
            size=size,
            sha256_digest=sha256_digest,
            meta=meta or {},
            label=label,
            entity_type=entity_type,
            created_by_id=db_agent.id,
            updated_by_id=db_agent.id,
        )
    with ensure_uniqueness(
        f"Asset with path {asset_create.path!r} already exists",
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
) -> AssetRead:
    """Mark an entity asset as deleted."""
    _ = entity_service.get_writable_entity(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    with ensure_result(f"Asset {asset_id} not found", error_code=ApiErrorCode.ASSET_NOT_FOUND):
        asset = repos.asset.update_entity_asset_status(
            entity_type=entity_type,
            entity_id=entity_id,
            asset_id=asset_id,
            asset_status=AssetStatus.DELETED,
        )
    return AssetRead.model_validate(asset)


def entity_asset_upload_directory(
    repos: RepositoryGroup,
    user_context: UserContext,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    s3_client: S3ClientDep,
    meta: dict | None,
    label: AssetLabel | None,
    files: FileList,
) -> tuple[dict[str, AnyUrl]]:
    entity = entity_service.get_writable_entity(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
    )

    # XXX: or do we want to use a user supplied name, and if so, how do we handle conflicts
    unique_name = str(create_uuid())
    full_path = build_s3_path(
        vlab_id=user_context.virtual_lab_id,
        proj_id=user_context.project_id,
        entity_type=entity_type,
        entity_id=entity_id,
        filename=unique_name,
        is_public=entity.authorized_public,
    )

    db_agent = get_or_create_user_agent(repos.db, user_profile=user_context.profile)

    with ensure_valid_schema(
        "Asset schema is invalid", error_code=ApiErrorCode.ASSET_INVALID_SCHEMA
    ):
        asset_create = AssetCreate(
            path="",
            full_path=full_path,
            is_directory=True,
            content_type="application/vnd.directory",
            size=-1,
            sha256_digest=None,
            meta=meta or {},
            label=label,
            entity_type=entity_type,
            created_by_id=db_agent.id,
            updated_by_id=db_agent.id,
        )

    with ensure_uniqueness(
        f"Asset with path {asset_create.path!r} already exists",
        error_code=ApiErrorCode.ASSET_DUPLICATED,
    ):
        asset_db = repos.asset.create_entity_asset(
            entity_id=entity_id,
            asset=asset_create,
        )

    urls = {}
    for f in files.files:
        sanitized_path = Path(os.path.normpath("/" / f)).relative_to("/")
        full_path = build_s3_path(
            vlab_id=user_context.virtual_lab_id,
            proj_id=user_context.project_id,
            entity_type=entity_type,
            entity_id=entity_id,
            filename= Path(unique_name) / sanitized_path,
            is_public=entity.authorized_public,
        )
        url = generate_presigned_url(
            s3_client=s3_client,
            operation="put_object",
            bucket_name=settings.S3_BUCKET_NAME,
            s3_key=full_path,
        )
        urls[f] = AnyUrl(url)

    return AssetRead.model_validate(asset_db), urls


def list_directory(
    repos: RepositoryGroup,
    user_context: UserContext,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
    s3_client: S3ClientDep,
) -> DetailedFileList:
    asset = get_entity_asset(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
        asset_id=asset_id,
    )

    ret = list_directory_with_details(
        s3_client,
        bucket_name=settings.S3_BUCKET_NAME,
        prefix=asset.full_path,
    )

    return DetailedFileList.model_validate({"files": ret})
