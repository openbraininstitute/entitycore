import uuid
from typing import Annotated

import sqlalchemy as sa
from fastapi_filter import FilterDepends

from app.db.model import BrainRegion, BrainRegionHierarchy
from app.filters.base import CustomFilter
from app.filters.common import NameFilterMixin


def _get_family_query(
    *, hierarchy_id: uuid.UUID, brain_region_id: uuid.UUID, with_ascendants=False
):
    """Create query for BrainRegions that returns ids.

    Can either traverse down (the default) or up (with_ascendants=True)
    """
    cte = (
        sa.select(BrainRegion.id, BrainRegion.parent_structure_id)
        .join(BrainRegionHierarchy, BrainRegion.hierarchy_id == BrainRegionHierarchy.id)
        .where(
            BrainRegion.id == brain_region_id,
            BrainRegionHierarchy.id == hierarchy_id,
        )
        .cte(recursive=True)
    )

    br_alias = sa.orm.aliased(BrainRegion)

    direction_join = br_alias.parent_structure_id == cte.c.id
    if with_ascendants:
        direction_join = br_alias.id == cte.c.parent_structure_id

    recurse = (
        sa.select(br_alias.id, br_alias.parent_structure_id)
        .join(cte, direction_join)
        .join(BrainRegionHierarchy, br_alias.hierarchy_id == BrainRegionHierarchy.id)
        .where(BrainRegionHierarchy.id == hierarchy_id)
    )

    query = cte.union_all(recurse)

    return query


def filter_by_hierarchy_and_region(
    *, query, model, hierarchy_id: uuid.UUID, brain_region_id: uuid.UUID, with_ascendants=False
):
    brain_region_query = _get_family_query(
        hierarchy_id=hierarchy_id,
        brain_region_id=brain_region_id,
        with_ascendants=with_ascendants,
    )
    query = query.filter(model.brain_region_id.in_(sa.select(brain_region_query.c.id)))
    return query


class BrainRegionFilter(NameFilterMixin, CustomFilter):
    id: uuid.UUID | None = None
    acronym: str | None = None
    annotation_value: int | None = None
    hierarchy_id: uuid.UUID | None = None

    order_by: list[str] = ["name"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = BrainRegion
        ordering_model_fields = ["name"]  # noqa: RUF012


BrainRegionFilterDep = Annotated[BrainRegionFilter, FilterDepends(BrainRegionFilter)]
