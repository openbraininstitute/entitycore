import json
import uuid
from collections import defaultdict

import sqlalchemy as sa
from fastapi import HTTPException, Response

from app.db.model import BrainRegion, BrainRegionHierarchyName
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.schemas.brain_region_hierarchy_name import BrainRegionHierarchyNameRead
from app.schemas.types import ListResponse, PaginationResponse


def read_many(
    db: SessionDep, pagination_request: PaginationQuery
) -> ListResponse[BrainRegionHierarchyNameRead]:
    query = sa.select(BrainRegionHierarchyName)

    data = db.execute(
        query.offset(pagination_request.offset).limit(pagination_request.page_size)
    ).scalars()

    total_items = db.execute(
        query.with_only_columns(sa.func.count(BrainRegionHierarchyName.id))
    ).scalar_one()

    response = ListResponse[BrainRegionHierarchyNameRead](
        data=[BrainRegionHierarchyNameRead.model_validate(d) for d in data],
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )

    return response


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
