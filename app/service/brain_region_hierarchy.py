import json
import uuid
from collections import defaultdict

import sqlalchemy as sa
from fastapi import HTTPException, Request, Response
from sqlalchemy.orm import joinedload, raiseload

import app.queries.common
from app.db.model import BrainRegion, BrainRegionHierarchy
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import FacetsDep, PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.brain_region_hierarchy import BrainRegionHierarchyFilterDep
from app.queries.factory import query_params_factory
from app.schemas.brain_region_hierarchy import (
    BrainRegionHierarchyAdminUpdate,
    BrainRegionHierarchyCreate,
    BrainRegionHierarchyRead,
)
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse
from app.utils.http_cache import CachedJson


def _load(query: sa.Select):
    return query.options(
        joinedload(BrainRegionHierarchy.species),
        joinedload(BrainRegionHierarchy.strain),
        joinedload(BrainRegionHierarchy.created_by),
        joinedload(BrainRegionHierarchy.updated_by),
        raiseload("*"),
    )


def read_many(
    db: SessionDep,
    pagination_request: PaginationQuery,
    brain_region_name_filter: BrainRegionHierarchyFilterDep,
    facets: FacetsDep,
) -> ListResponse[BrainRegionHierarchyRead]:
    db_model_class = BrainRegionHierarchy
    facet_keys = filter_keys = [
        "species",
        "strain",
    ]
    name_to_facet_query_params, join_specs, aliases = query_params_factory(
        db_model_class=db_model_class,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
    )
    return app.queries.common.router_read_many(
        db=db,
        db_model_class=db_model_class,
        authorized_project_id=None,
        with_search=None,
        with_in_brain_region=None,
        facets=facets,
        aliases=aliases,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        pagination_request=pagination_request,
        response_schema_class=BrainRegionHierarchyRead,
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=brain_region_name_filter,
        join_specs=join_specs,
    )


admin_read_many = read_many


def read_one(id_: uuid.UUID, db: SessionDep) -> BrainRegionHierarchyRead:
    return app.queries.common.router_read_one(
        id_=id_,
        db=db,
        db_model_class=BrainRegionHierarchy,
        user_context=None,
        response_schema_class=BrainRegionHierarchyRead,
        apply_operations=_load,
    )


admin_read_one = read_one


def create_one(
    *,
    db: SessionDep,
    json_model: BrainRegionHierarchyCreate,
    user_context: AdminContextDep,
) -> BrainRegionHierarchyRead:
    return app.queries.common.router_create_one(
        db=db,
        db_model_class=BrainRegionHierarchy,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=BrainRegionHierarchyRead,
        apply_operations=_load,
    )


def update_one(
    db: SessionDep,
    user_context: AdminContextDep,
    id_: uuid.UUID,
    json_model: BrainRegionHierarchyAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> BrainRegionHierarchyRead:
    return app.queries.common.router_update_one(
        id_=id_,
        db=db,
        db_model_class=BrainRegionHierarchy,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=BrainRegionHierarchyRead,
        apply_operations=_load,
        check_authorized_project=False,
    )


admin_update_one = update_one


def delete_one(
    db: SessionDep,
    id_: uuid.UUID,
    user_context: AdminContextDep,  # ruff:ignore[unused-function-argument]
) -> DeleteResponse:
    return app.queries.common.router_admin_delete_one(
        id_=id_,
        db=db,
        db_model_class=BrainRegionHierarchy,
    )


class _JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, uuid.UUID):
            return str(o)
        return json.JSONEncoder.default(self, o)


# Hierarchies aren't updated, so the cache doesn't need any expiration.
HIERARCHY_CACHE: dict[uuid.UUID, CachedJson] = {}


def read_hierarchy(
    *,
    request: Request,
    db: SessionDep,
    id_: uuid.UUID,
) -> Response:
    if (cached := HIERARCHY_CACHE.get(id_)) is None:
        cached = CachedJson.from_content(_build_hierarchy_json(db=db, id_=id_))
        HIERARCHY_CACHE[id_] = cached
    return cached.to_response(request)


def _build_hierarchy_json(*, db: SessionDep, id_: uuid.UUID) -> bytes:
    query = sa.select(BrainRegion).filter(BrainRegion.hierarchy_id == id_)

    data = db.execute(query).scalars().fetchall()

    if not data:
        raise HTTPException(status_code=404, detail=f"No hierarchy named {id_}")

    parent_map = defaultdict(list)
    for region in data:
        parent_map[region.parent_structure_id].append(region)

    def build_tree(parent_id):
        children = sorted(parent_map.get(parent_id, []), key=lambda n: n.name)
        return [
            {
                "id": node.id,
                "annotation_value": node.annotation_value,
                "name": node.name,
                "acronym": node.acronym,
                "color_hex_triplet": node.color_hex_triplet,
                "parent_structure_id": node.parent_structure_id,
                "hierarchy_id": node.hierarchy_id,
                "children": build_tree(node.id),
            }
            for node in children
        ]

    tree = build_tree(None)[0]
    return json.dumps(tree, cls=_JSONEncoder).encode()
