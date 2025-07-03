from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import EModel
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    BrainRegionFilterMixin,
    EntityFilterMixin,
    ETypeClassFilterMixin,
    MTypeClassFilterMixin,
    NameFilterMixin,
    SpeciesFilterMixin,
)
from app.filters.morphology import MorphologyFilter, NestedExemplarMorphologyFilterDep


class EModelFilter(
    CustomFilter,
    BrainRegionFilterMixin,
    EntityFilterMixin,
    MTypeClassFilterMixin,
    ETypeClassFilterMixin,
    SpeciesFilterMixin,
    NameFilterMixin,
):
    score__lte: float | None = None
    score__gte: float | None = None

    exemplar_morphology: Annotated[MorphologyFilter | None, NestedExemplarMorphologyFilterDep] = (
        None
    )

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = EModel
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


# Dependencies
EModelFilterDep = Annotated[EModelFilter, FilterDepends(EModelFilter)]
# Nested dependencies
NestedEModelFilterDep = FilterDepends(with_prefix("emodel", EModelFilter))
