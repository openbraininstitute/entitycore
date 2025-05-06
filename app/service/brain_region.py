import json
import uuid
from collections import defaultdict

import sqlalchemy as sa
from fastapi import HTTPException, Response

from app.db.model import BrainRegion, BrainRegionHierarchyName
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.filters.brain_region import BrainRegionFilterDep
from app.schemas.base import BrainRegionRead
from app.schemas.types import ListResponse, PaginationResponse


class _JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, uuid.UUID):
            return str(o)
        return json.JSONEncoder.default(self, o)


def read_hierarchy_name_hierarchy(
    *,
    db: SessionDep,
    hierarchy_name: str,
):
    query = (
        sa.select(BrainRegion)
        .join(BrainRegionHierarchyName)
        .filter(BrainRegionHierarchyName.name == hierarchy_name)
    )

    data = db.execute(query).scalars()

    if not data:
        raise HTTPException(status_code=404, detail=f"No hierarchy named {hierarchy_name}")

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

    tree = build_tree(BrainRegion.ROOT_PARENT_UUID)[0]
    js = json.dumps(tree, cls=_JSONEncoder)
    response = Response(content=js, media_type="application/json")
    return response


def read_many(
    *,
    db: SessionDep,
    pagination_request: PaginationQuery,
    brain_region_filter: BrainRegionFilterDep,
) -> ListResponse[BrainRegionRead]:
    query = sa.select(BrainRegion)
    query = brain_region_filter.filter(query)

    data = db.execute(
        query.offset(pagination_request.offset).limit(pagination_request.page_size)
    ).scalars()

    total_items = db.execute(query.with_only_columns(sa.func.count(BrainRegion.id))).scalar_one()

    response = ListResponse[BrainRegionRead](
        data=[BrainRegionRead.model_validate(d) for d in data],
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )
    return response


def read_one(db: SessionDep, id_: uuid.UUID) -> BrainRegionRead:
    with ensure_result(error_message="Brain region not found"):
        stmt = sa.select(BrainRegion).filter(BrainRegion.id == id_)
        row = db.execute(stmt).scalar_one()
    return BrainRegionRead.model_validate(row)
