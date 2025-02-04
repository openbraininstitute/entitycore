from uuid import UUID

from app.db.types import AssetStatus, EntityType
from app.errors import ApiError, ApiErrorCode, ensure_result
from app.repository.group import RepositoryGroup
from app.schemas.asset import AssetCreate, AssetRead


def _check_entity_auth(
    repos: RepositoryGroup,
    entity_type: EntityType,
    entity_id: int,
    proj_id: UUID,  # noqa: ARG001
) -> None:
    result = repos.entity.get_entity(entity_type=entity_type, entity_id=entity_id)
    if not result:
        raise ApiError(
            message="Entity not found",
            error_code=ApiErrorCode.ENTITY_NOT_FOUND,
        )
    # if not result.authorized_public and result.authorized_project_id != proj_id:
    #     raise ApiError(
    #         message="Entity forbidden",
    #         error_code=ApiErrorCode.ENTITY_FORBIDDEN,
    #     )


def get_entity_assets(
    repos: RepositoryGroup,
    entity_type: EntityType,
    entity_id: int,
    proj_id: UUID,
) -> list[AssetRead]:
    """Return the list of assets associated with a specific entity."""
    _check_entity_auth(repos=repos, entity_type=entity_type, entity_id=entity_id, proj_id=proj_id)
    return [
        AssetRead.model_validate(row)
        for row in repos.asset.get_entity_assets(entity_type=entity_type, entity_id=entity_id)
    ]


def get_entity_asset(
    repos: RepositoryGroup,
    entity_type: EntityType,
    entity_id: int,
    asset_id: UUID,
    proj_id: UUID,
) -> AssetRead:
    """Return an asset associated with a specific entity."""
    _check_entity_auth(repos=repos, entity_type=entity_type, entity_id=entity_id, proj_id=proj_id)
    with ensure_result(f"Asset {asset_id} not found"):
        asset = repos.asset.get_entity_asset(
            entity_type=entity_type, entity_id=entity_id, asset_id=asset_id
        )
    return AssetRead.model_validate(asset)


def create_entity_asset(
    repos: RepositoryGroup,
    entity_type: EntityType,
    entity_id: int,
    proj_id: UUID,
    asset: AssetCreate,
) -> AssetRead:
    """Create an asset for an entity."""
    _check_entity_auth(repos=repos, entity_type=entity_type, entity_id=entity_id, proj_id=proj_id)
    asset_db = repos.asset.create_entity_asset(
        entity_type=entity_type,
        entity_id=entity_id,
        asset=asset,
    )
    return AssetRead.model_validate(asset_db)


def delete_entity_asset(
    repos: RepositoryGroup,
    entity_type: EntityType,
    entity_id: int,
    asset_id: UUID,
    proj_id: UUID,
) -> AssetRead:
    """Mark an entity asset as deleted."""
    _check_entity_auth(repos=repos, entity_type=entity_type, entity_id=entity_id, proj_id=proj_id)
    with ensure_result(f"Asset {asset_id} not found"):
        asset = repos.asset.update_entity_asset_status(
            entity_type=entity_type,
            entity_id=entity_id,
            asset_id=asset_id,
            asset_status=AssetStatus.DELETED,
        )
    return AssetRead.model_validate(asset)
