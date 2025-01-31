from http import HTTPStatus

from app.db.types import AssetStatus, EntityType
from app.errors import ApiError, ApiErrorCode, ensure_result, ensure_uniqueness
from app.repository.group import RepositoryGroup
from app.schemas.asset import AssetCreate, AssetRead
from app.schemas.base import ProjectContext


def _check_entity_auth(
    repos: RepositoryGroup,
    project_context: ProjectContext,  # noqa: ARG001
    entity_type: EntityType,
    entity_id: int,
) -> None:
    result = repos.entity.get_entity(entity_type=entity_type, entity_id=entity_id)
    if not result:
        raise ApiError(
            message="Entity not found",
            error_code=ApiErrorCode.ENTITY_NOT_FOUND,
            http_status_code=HTTPStatus.NOT_FOUND,
        )
    # if (
    #         not result.authorized_public
    #         and result.authorized_project_id != project_context.project_id
    # ):
    #     raise ApiError(
    #         message="Entity forbidden",
    #         error_code=ApiErrorCode.ENTITY_FORBIDDEN,
    #         http_status_code=HTTPStatus.FORBIDDEN,
    #     )


def get_entity_assets(
    repos: RepositoryGroup,
    project_context: ProjectContext,
    entity_type: EntityType,
    entity_id: int,
) -> list[AssetRead]:
    """Return the list of assets associated with a specific entity."""
    _check_entity_auth(
        repos=repos, entity_type=entity_type, entity_id=entity_id, project_context=project_context
    )
    return [
        AssetRead.model_validate(row)
        for row in repos.asset.get_entity_assets(entity_type=entity_type, entity_id=entity_id)
    ]


def get_entity_asset(
    repos: RepositoryGroup,
    project_context: ProjectContext,
    entity_type: EntityType,
    entity_id: int,
    asset_id: int,
) -> AssetRead:
    """Return an asset associated with a specific entity."""
    _check_entity_auth(
        repos=repos, entity_type=entity_type, entity_id=entity_id, project_context=project_context
    )
    with ensure_result(f"Asset {asset_id} not found", error_code=ApiErrorCode.ASSET_NOT_FOUND):
        asset = repos.asset.get_entity_asset(
            entity_type=entity_type, entity_id=entity_id, asset_id=asset_id
        )
    return AssetRead.model_validate(asset)


def create_entity_asset(
    repos: RepositoryGroup,
    project_context: ProjectContext,
    entity_type: EntityType,
    entity_id: int,
    asset: AssetCreate,
) -> AssetRead:
    """Create an asset for an entity."""
    _check_entity_auth(
        repos=repos, entity_type=entity_type, entity_id=entity_id, project_context=project_context
    )
    with ensure_uniqueness(
        f"Asset with path {asset.path!r} already exists",
        error_code=ApiErrorCode.ASSET_DUPLICATED,
    ):
        asset_db = repos.asset.create_entity_asset(
            entity_id=entity_id,
            asset=asset,
        )
    return AssetRead.model_validate(asset_db)


def delete_entity_asset(
    repos: RepositoryGroup,
    project_context: ProjectContext,
    entity_type: EntityType,
    entity_id: int,
    asset_id: int,
) -> AssetRead:
    """Mark an entity asset as deleted."""
    _check_entity_auth(
        repos=repos, entity_type=entity_type, entity_id=entity_id, project_context=project_context
    )
    with ensure_result(f"Asset {asset_id} not found", error_code=ApiErrorCode.ASSET_NOT_FOUND):
        asset = repos.asset.update_entity_asset_status(
            entity_type=entity_type,
            entity_id=entity_id,
            asset_id=asset_id,
            asset_status=AssetStatus.DELETED,
        )
    return AssetRead.model_validate(asset)
