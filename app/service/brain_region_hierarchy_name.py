import json
import uuid
from collections import defaultdict

import sqlalchemy as sa
from fastapi import HTTPException, Response

import app.queries.common
from app.db.model import BrainRegion, BrainRegionHierarchyName
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.filters.brain_region_name import BrainRegionNameFilterDep
from app.schemas.brain_region_hierarchy_name import BrainRegionHierarchyNameRead
from app.schemas.types import ListResponse


def read_many(
    db: SessionDep,
    pagination_request: PaginationQuery,
    brain_region_name_filter: BrainRegionNameFilterDep,
) -> ListResponse[BrainRegionHierarchyNameRead]:
    return app.queries.common.router_read_many(
        db=db,
        db_model_class=BrainRegionHierarchyName,
        authorized_project_id=None,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=None,
        apply_filter_query_operations=None,
        apply_data_query_operations=None,
        pagination_request=pagination_request,
        response_schema_class=BrainRegionHierarchyNameRead,
        name_to_facet_query_params=None,
        filter_model=brain_region_name_filter,
    )


def read_one(id_: uuid.UUID, db: SessionDep) -> BrainRegionHierarchyNameRead:
    with ensure_result(error_message="Brain Region Hierarchy Name not found"):
        stmt = sa.select(BrainRegionHierarchyName).filter(BrainRegionHierarchyName.id == id_)
        row = db.execute(stmt).scalar_one()
    return BrainRegionHierarchyNameRead.model_validate(row)


class _JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, uuid.UUID):
            return str(o)
        return json.JSONEncoder.default(self, o)


def read_hierarchy_name_hierarchy(
    *,
    db: SessionDep,
    id_: str,
):
    query = (
        sa.select(BrainRegion)
        .join(BrainRegionHierarchyName)
        .filter(BrainRegionHierarchyName.id == id_)
    )

    data = db.execute(query).scalars()

    if not data:
        raise HTTPException(status_code=404, detail=f"No hierarchy named {id_}")

    parent_map = defaultdict(list)
    for region in data:
        parent_map[region.parent_structure_id].append(region)

    def build_tree(parent_id):
        children = parent_map.get(parent_id, [])
        return [
            {
                "id": node.id,
                "hierarchy_id": node.hierarchy_id,
                "name": node.name,
                "acronym": node.acronym,
                "color_hex_triplet": node.color_hex_triplet,
                "parent_structure_id": node.parent_structure_id,
                "children": build_tree(node.id),
            }
            for node in children
        ]

    tree = build_tree(None)[0]
    js = json.dumps(tree, cls=_JSONEncoder)
    response = Response(content=js, media_type="application/json")
    return response
