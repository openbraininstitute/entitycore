import uuid
from http import HTTPStatus
from typing import Annotated

from fastapi import Form, HTTPException, UploadFile
from starlette.responses import RedirectResponse

from app.config import settings, storages
from app.db.model import Asset, Entity
from app.db.types import AssetLabel, AssetStatus, ContentType, EntityType, StorageType
from app.db.utils import RESOURCE_TYPE_TO_CLASS
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ApiError, ApiErrorCode, ensure_result, ensure_uniqueness, ensure_valid_schema
from app.filters.asset import AssetFilterDep
from app.queries import crud
from app.queries.common import get_or_create_user_agent, router_admin_delete_one, router_read_many
from app.repository.group import RepositoryGroup
from app.routers.types import EntityRoute, ResourceRoute
from app.schemas.asset import (
    AssetCreate,
    AssetRead,
)
from app.schemas.auth import UserContextWithProjectId
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse
from app.service.asset import create_asset_download_redirect
from app.utils.files import calculate_sha256_digest, get_content_type
from app.utils.routers import entity_route_to_type, route_to_type
from app.utils.s3 import (
    StorageClientFactory,
    build_s3_path,
    upload_to_s3,
    validate_filename,
    validate_filesize,
)


def delete_one(
    db: SessionDep,
    route: ResourceRoute,
    id_: uuid.UUID,
) -> DeleteResponse:
    resource_type = route_to_type(route)
    return router_admin_delete_one(
        id_=id_,
        db=db,
        db_model_class=RESOURCE_TYPE_TO_CLASS[resource_type],
    )


def get_entity_asset(
    repos: RepositoryGroup,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> AssetRead:
    """Return an asset associated with a specific entity."""
    with ensure_result(f"Asset {asset_id} not found", error_code=ApiErrorCode.ASSET_NOT_FOUND):
        asset = repos.asset.get_entity_asset(
            entity_type=entity_type,
            entity_id=entity_id,
            asset_id=asset_id,
            include_deleted=True,
        )
    return AssetRead.model_validate(asset)


def get_entity_assets(
    repos: RepositoryGroup,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    pagination_request: PaginationQuery,
    filter_model: AssetFilterDep,
) -> ListResponse[AssetRead]:
    """Return the list of assets associated with a specific entity."""
    db_model_class = Asset
    entity_type = entity_route_to_type(entity_route)
    apply_filter_query_operations = lambda q: q.join(Entity, Entity.id == Asset.entity_id).where(
        Asset.entity_id == entity_id,
        Entity.type == entity_type.name,
    )
    name_to_facet_query_params = filter_joins = None
    return router_read_many(
        db=repos.db,
        db_model_class=db_model_class,
        authorized_project_id=None,
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


def download_entity_asset(
    repos: RepositoryGroup,
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
        entity_type=entity_route_to_type(entity_route),
        entity_id=entity_id,
        asset_id=asset_id,
    )
    return create_asset_download_redirect(
        asset=asset,
        storage_client_factory=storage_client_factory,
        asset_path=asset_path,
    )


def upload_entity_asset(
    repos: RepositoryGroup,
    user_context: UserContextWithProjectId,
    storage_client_factory: StorageClientFactory,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    file: UploadFile,
    label: Annotated[AssetLabel, Form()],
    meta: Annotated[dict | None, Form()] = None,
):
    storage = storages[StorageType.aws_s3_internal]  # hardcoded for now
    s3_client = storage_client_factory(storage)
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
        content_type = get_content_type(file)
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

    sha256_digest = calculate_sha256_digest(file)
    asset_read = create_entity_asset(
        repos=repos,
        user_context=user_context,
        entity_type=entity_route_to_type(entity_route),
        entity_id=entity_id,
        filename=file.filename,
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
) -> AssetRead:
    """Create an asset for an entity."""
    entity = crud.get_identifiable_one(
        db=repos.db,
        db_model_class=Entity,
        id_=entity_id,
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
            status=status,
        )
    return AssetRead.model_validate(asset_db)
