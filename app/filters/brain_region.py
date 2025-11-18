import uuid
from enum import StrEnum, auto
from typing import Annotated

import sqlalchemy as sa
from fastapi_filter import with_prefix
from sqlalchemy.orm import aliased

from app.db.model import BrainRegion, BrainRegionHierarchy
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import IdFilterMixin, NameFilterMixin


class WithinBrainRegionDirection(StrEnum):
    ascendants = auto()
    descendants = auto()
    ascendants_and_descendants = auto()


def get_family_query(
    *, hierarchy_id: uuid.UUID, brain_region_id: uuid.UUID, direction: WithinBrainRegionDirection
) -> sa.CTE:
    """Create query for BrainRegions that returns ids."""
    cte = (
        sa.select(BrainRegion.id, BrainRegion.parent_structure_id)
        .join(BrainRegionHierarchy, BrainRegion.hierarchy_id == BrainRegionHierarchy.id)
        .where(
            BrainRegion.id == brain_region_id,
            BrainRegionHierarchy.id == hierarchy_id,
        )
        .cte(recursive=True)
    )

    br_alias = aliased(BrainRegion)

    if direction == WithinBrainRegionDirection.ascendants:
        join_direction = br_alias.id == cte.c.parent_structure_id
    elif direction == WithinBrainRegionDirection.descendants:
        join_direction = br_alias.parent_structure_id == cte.c.id
    elif direction == WithinBrainRegionDirection.ascendants_and_descendants:
        # union of ascendants and descendants
        return (
            sa.select(
                get_family_query(
                    hierarchy_id=hierarchy_id,
                    brain_region_id=brain_region_id,
                    direction=WithinBrainRegionDirection.ascendants,
                ).c.id
            )
            .union_all(
                sa.select(
                    get_family_query(
                        hierarchy_id=hierarchy_id,
                        brain_region_id=brain_region_id,
                        direction=WithinBrainRegionDirection.descendants,
                    ).c.id
                )
            )
            .cte()
        )

    recurse = (
        sa.select(br_alias.id, br_alias.parent_structure_id)
        .join(cte, join_direction)
        .join(BrainRegionHierarchy, br_alias.hierarchy_id == BrainRegionHierarchy.id)
        .where(BrainRegionHierarchy.id == hierarchy_id)
    )

    query = cte.union_all(recurse)

    return query


def filter_by_hierarchy_and_region(
    *,
    query,
    model,
    hierarchy_id: uuid.UUID,
    brain_region_id: uuid.UUID,
    direction: WithinBrainRegionDirection,
):
    brain_region_query = get_family_query(
        hierarchy_id=hierarchy_id,
        brain_region_id=brain_region_id,
        direction=direction,
    )
    query = query.join(brain_region_query, model.brain_region_id == brain_region_query.c.id)
    return query


class NestedBrainRegionFilter(IdFilterMixin, NameFilterMixin, CustomFilter):
    acronym: str | None = None
    acronym__in: list[str] | None = None
    annotation_value: int | None = None
    hierarchy_id: uuid.UUID | None = None

    class Constants(CustomFilter.Constants):
        model = BrainRegion


class BrainRegionFilter(NestedBrainRegionFilter):
    order_by: list[str] = ["name"]  # noqa: RUF012

    class Constants(NestedBrainRegionFilter.Constants):
        ordering_model_fields = ["name"]  # noqa: RUF012


BrainRegionFilterDep = Annotated[BrainRegionFilter, FilterDepends(BrainRegionFilter)]
NestedBrainRegionFilterDep = FilterDepends(with_prefix("brain_region", NestedBrainRegionFilter))


class BrainRegionFilterMixin:
    brain_region: Annotated[NestedBrainRegionFilter | None, NestedBrainRegionFilterDep] = None
