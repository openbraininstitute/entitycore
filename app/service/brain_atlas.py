import threading
import time
import uuid

import cachetools
import sqlalchemy as sa
from cachetools.keys import hashkey
from fastapi import Request, Response
from pydantic import TypeAdapter
from sqlalchemy.orm import joinedload, raiseload, selectinload

import app.queries.common
from app.config import settings
from app.db.model import BrainAtlas, BrainAtlasRegion, Contribution
from app.dependencies.auth import AdminContextDep, UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    ExpandDep,
    PaginationQuery,
)
from app.dependencies.db import SessionDep
from app.filters.brain_atlas import BrainAtlasFilterDep, BrainAtlasRegionFilterDep
from app.queries.expand import EntityExpand
from app.queries.factory import query_params_factory
from app.schemas.brain_atlas import (
    BrainAtlasAdminUpdate,
    BrainAtlasCreate,
    BrainAtlasRead,
    BrainAtlasUpdate,
)
from app.schemas.brain_atlas_region import BrainAtlasRegionRead
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse
from app.utils.http_cache import CachedJson

_REGIONS_ADAPTER = TypeAdapter(ListResponse[BrainAtlasRegionRead])


def _regions_cache_key(
    *, atlas_id: uuid.UUID, scope_project_id: uuid.UUID | None, _query_params: tuple, **_
) -> tuple:
    return hashkey(atlas_id, scope_project_id, _query_params)


@cachetools.cached(
    cache=cachetools.TTLCache(
        maxsize=settings.BRAIN_ATLAS_REGIONS_CACHE_MAXSIZE_BYTES,
        ttl=settings.BRAIN_ATLAS_REGIONS_CACHE_TTL_SECONDS,
        timer=time.monotonic,
        getsizeof=CachedJson.size,
    ),
    key=_regions_cache_key,
    condition=threading.Condition(),  # concurrent requests wait for the first to fill the cache
)
def _read_many_region_json(
    *,
    atlas_id: uuid.UUID,
    scope_project_id: uuid.UUID | None,
    _query_params: tuple,
    db: SessionDep,
    pagination_request: PaginationQuery,
    brain_atlas_region_filter: BrainAtlasRegionFilterDep,
) -> CachedJson:
    result = app.queries.common.router_read_many(
        db=db,
        db_model_class=BrainAtlasRegion,
        authorized_project_id=scope_project_id,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=None,
        apply_filter_query_operations=lambda q: q.filter(
            BrainAtlasRegion.brain_atlas_id == atlas_id
        ),
        apply_data_query_operations=lambda s: s.options(selectinload(BrainAtlasRegion.assets)),
        pagination_request=pagination_request,
        response_schema_class=BrainAtlasRegionRead,
        name_to_facet_query_params=None,
        filter_model=brain_atlas_region_filter,
    )
    return CachedJson.from_content(_REGIONS_ADAPTER.dump_json(result, by_alias=True))


def _has_private_regions(
    *, db: SessionDep, atlas_id: uuid.UUID, project_id: uuid.UUID | None
) -> bool:
    if project_id is None:
        return False
    query = (
        sa.select(sa.literal(1))
        .select_from(BrainAtlasRegion)
        .where(
            BrainAtlasRegion.brain_atlas_id == atlas_id,
            BrainAtlasRegion.authorized_project_id == project_id,
            BrainAtlasRegion.authorized_public.is_(False),
        )
        .exists()
    )
    return db.execute(sa.select(query)).scalar_one()


def _load_brain_atlas(query: sa.Select):
    return query.options(
        joinedload(BrainAtlas.created_by),
        joinedload(BrainAtlas.updated_by),
        joinedload(BrainAtlas.species),
        joinedload(BrainAtlas.strain),
        selectinload(BrainAtlas.assets),
        selectinload(BrainAtlas.contributions).options(
            selectinload(Contribution.agent),
            selectinload(Contribution.role),
        ),
        raiseload("*"),
    )


def _read_many(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: BrainAtlasFilterDep,
    expand: set[EntityExpand] | None,
    check_authorized_project: bool,
) -> ListResponse[BrainAtlasRead]:
    facet_keys = []
    filter_keys = [
        "species",
        "strain",
    ]
    name_to_facet_query_params, join_specs, aliases = query_params_factory(
        db_model_class=BrainAtlas,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
    )

    return app.queries.common.router_read_many(
        db=db,
        db_model_class=BrainAtlas,
        authorized_project_id=user_context.project_id,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=aliases,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load_brain_atlas,
        pagination_request=pagination_request,
        response_schema_class=BrainAtlasRead,
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=filter_model,
        join_specs=join_specs,
        check_authorized_project=check_authorized_project,
        expand=expand,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: BrainAtlasFilterDep,
    expand: ExpandDep = None,
) -> ListResponse[BrainAtlasRead]:
    return _read_many(
        user_context=user_context,
        db=db,
        pagination_request=pagination_request,
        filter_model=filter_model,
        expand=expand,
        check_authorized_project=True,
    )


def admin_read_many(
    user_context: AdminContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: BrainAtlasFilterDep,
    expand: ExpandDep = None,
) -> ListResponse[BrainAtlasRead]:
    return _read_many(
        db=db,
        user_context=user_context,
        pagination_request=pagination_request,
        filter_model=filter_model,
        expand=expand,
        check_authorized_project=False,
    )


def read_one(
    user_context: UserContextDep,
    id_: uuid.UUID,
    db: SessionDep,
    expand: ExpandDep = None,
) -> BrainAtlasRead:
    return app.queries.common.router_read_one(
        id_=id_,
        db=db,
        db_model_class=BrainAtlas,
        user_context=user_context,
        response_schema_class=BrainAtlasRead,
        apply_operations=_load_brain_atlas,
        expand=expand,
    )


def admin_read_one(db: SessionDep, id_: uuid.UUID, expand: ExpandDep = None) -> BrainAtlasRead:
    return app.queries.common.router_read_one(
        id_=id_,
        db=db,
        db_model_class=BrainAtlas,
        user_context=None,
        response_schema_class=BrainAtlasRead,
        apply_operations=_load_brain_atlas,
        expand=expand,
    )


def create_one(
    db: SessionDep,
    json_model: BrainAtlasCreate,
    user_context: UserContextWithProjectIdDep,
) -> BrainAtlasRead:
    return app.queries.common.router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=BrainAtlas,
        response_schema_class=BrainAtlasRead,
        apply_operations=_load_brain_atlas,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: BrainAtlasUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> BrainAtlasRead:
    return app.queries.common.router_update_one(
        id_=id_,
        db=db,
        db_model_class=BrainAtlas,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=BrainAtlasRead,
        apply_operations=_load_brain_atlas,
        check_authorized_project=True,
    )


def admin_update_one(
    user_context: AdminContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: BrainAtlasAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> BrainAtlasRead:
    return app.queries.common.router_update_one(
        id_=id_,
        db=db,
        db_model_class=BrainAtlas,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=BrainAtlasRead,
        apply_operations=_load_brain_atlas,
        check_authorized_project=False,
    )


def delete_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> DeleteResponse:
    return app.queries.common.router_user_delete_one(
        id_=id_,
        db=db,
        db_model_class=BrainAtlas,
        user_context=user_context,
    )


def read_many_region(
    request: Request,
    user_context: UserContextDep,
    atlas_id: uuid.UUID,
    db: SessionDep,
    pagination_request: PaginationQuery,
    brain_atlas_region_filter: BrainAtlasRegionFilterDep,
) -> Response:
    # Projects without private regions share the cached public regions.
    has_private_regions = _has_private_regions(
        db=db, atlas_id=atlas_id, project_id=user_context.project_id
    )
    cached = _read_many_region_json(
        atlas_id=atlas_id,
        scope_project_id=user_context.project_id if has_private_regions else None,
        _query_params=tuple(sorted(request.query_params.multi_items())),
        db=db,
        pagination_request=pagination_request,
        brain_atlas_region_filter=brain_atlas_region_filter,
    )
    return cached.to_response(request)


def read_one_region(
    user_context: UserContextDep, atlas_id: uuid.UUID, atlas_region_id: uuid.UUID, db: SessionDep
) -> BrainAtlasRegionRead:
    return app.queries.common.router_read_one(
        id_=atlas_region_id,
        db=db,
        db_model_class=BrainAtlasRegion,
        user_context=user_context,
        response_schema_class=BrainAtlasRegionRead,
        apply_operations=lambda select: select.filter(
            BrainAtlasRegion.brain_atlas_id == atlas_id
        ).options(selectinload(BrainAtlasRegion.assets)),
    )
