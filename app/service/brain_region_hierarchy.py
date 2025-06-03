import json
import uuid
from collections import defaultdict

import sqlalchemy as sa
from fastapi import HTTPException, Response

import app.queries.common
from app.db.model import BrainRegion, BrainRegionHierarchy
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.brain_region_hierarchy import BrainRegionHierarchyFilterDep
from app.schemas.brain_region_hierarchy import BrainRegionHierarchyRead
from app.schemas.types import ListResponse


def read_many(
    db: SessionDep,
    pagination_request: PaginationQuery,
    brain_region_name_filter: BrainRegionHierarchyFilterDep,
) -> ListResponse[BrainRegionHierarchyRead]:
    return app.queries.common.router_read_many(
        db=db,
        db_model_class=BrainRegionHierarchy,
        authorized_project_id=None,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=None,
        apply_filter_query_operations=None,
        apply_data_query_operations=None,
        pagination_request=pagination_request,
        response_schema_class=BrainRegionHierarchyRead,
        name_to_facet_query_params=None,
        filter_model=brain_region_name_filter,
    )


def read_one(id_: uuid.UUID, db: SessionDep) -> BrainRegionHierarchyRead:
    return app.queries.common.router_read_one(
        id_=id_,
        db=db,
        db_model_class=BrainRegionHierarchy,
        authorized_project_id=None,
        response_schema_class=BrainRegionHierarchyRead,
        apply_operations=None,
    )


class _JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, uuid.UUID):
            return str(o)
        return json.JSONEncoder.default(self, o)


def read_hierarchy(
    *,
    db: SessionDep,
    id_: str,
):
    query = sa.select(BrainRegion).join(BrainRegionHierarchy).filter(BrainRegionHierarchy.id == id_)

    data = db.execute(query).scalars()

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
                "children": build_tree(node.id),
            }
            for node in children
        ]

    tree = build_tree(None)[0]
    js = json.dumps(tree, cls=_JSONEncoder)
    response = Response(content=js, media_type="application/json")
    return response
