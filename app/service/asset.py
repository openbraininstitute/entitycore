import uuid

from app.config import settings
from app.db.types import AssetStatus, EntityType
from app.errors import ApiErrorCode, ensure_result, ensure_uniqueness
from app.repository.group import RepositoryGroup
from app.schemas.asset import AssetCreate, AssetRead
from app.schemas.auth import UserContext, UserContextWithProjectId
from app.service import entity as entity_service
from app.utils.s3 import build_s3_path


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
) -> AssetRead:
    """Create an asset for an entity."""
    entity = entity_service.get_writable_entity(
        repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    bucket_name = settings.S3_BUCKET_NAME
    full_path = build_s3_path(
        vlab_id=user_context.virtual_lab_id,
        proj_id=user_context.project_id,
        entity_type=entity_type,
        entity_id=entity_id,
        filename=filename,
        is_public=entity.authorized_public,
    )
    asset_create = AssetCreate(
        path=filename,
        full_path=full_path,
        bucket_name=bucket_name,
        is_directory=False,
        content_type=content_type,
        size=size,
        sha256_digest=sha256_digest,
        meta=meta or {},
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
