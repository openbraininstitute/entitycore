from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import EModel
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    BrainRegionFilterMixin,
    EntityFilterMixin,
    ETypeClassFilterMixin,
    IdFilterMixin,
    MTypeClassFilterMixin,
    NameFilterMixin,
    NestedBrainRegionFilter,
    NestedETypeClassFilter,
    NestedMTypeClassFilter,
    SpeciesFilterMixin,
)
from app.filters.morphology import NestedMorphologyFilter


class NestedEModelFilter(
    IdFilterMixin,
    NameFilterMixin,
    CustomFilter,
):
    score__lte: float | None = None
    score__gte: float | None = None

    brain_region: Annotated[
        NestedBrainRegionFilter | None,
        FilterDepends(with_prefix("emodel__brain_region", NestedBrainRegionFilter)),
    ] = None
    mtype: Annotated[
        NestedMTypeClassFilter,
        FilterDepends(with_prefix("emodel__mtype", NestedMTypeClassFilter)),
    ]
    etype: Annotated[
        NestedETypeClassFilter,
        FilterDepends(with_prefix("emodel__etype", NestedETypeClassFilter)),
    ]
    exemplar_morphology: Annotated[
        NestedMorphologyFilter | None,
        FilterDepends(with_prefix("emodel__exemplar_morphology", NestedMorphologyFilter)),
    ] = None

    class Constants(CustomFilter.Constants):
        model = EModel


class EModelFilter(
    BrainRegionFilterMixin,
    EntityFilterMixin,
    MTypeClassFilterMixin,
    ETypeClassFilterMixin,
    SpeciesFilterMixin,
    NameFilterMixin,
    CustomFilter,
):
    score__lte: float | None = None
    score__gte: float | None = None

    exemplar_morphology: Annotated[
        NestedMorphologyFilter | None,
        FilterDepends(with_prefix("exemplar_morphology", NestedMorphologyFilter)),
    ] = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = EModel
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


# Dependencies
EModelFilterDep = Annotated[EModelFilter, FilterDepends(EModelFilter)]
# Nested dependencies
NestedEModelFilterDep = FilterDepends(with_prefix("emodel", NestedEModelFilter))
