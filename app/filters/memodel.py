from typing import Annotated

from fastapi_filter import FilterDepends, with_prefix

from app.db.model import MEModel, ValidationStatus
from app.filters.base import CustomFilter
from app.filters.common import (
    BrainRegionFilterMixin,
    EntityFilterMixin,
    ETypeClassFilterMixin,
    MTypeClassFilterMixin,
    SpeciesFilterMixin,
)
from app.filters.emodel import EModelFilter, NestedEModelFilterDep
from app.filters.morphology import MorphologyFilter, NestedMorphologyFilterDep


class MEModelFilter(
    CustomFilter,
    SpeciesFilterMixin,
    EntityFilterMixin,
    MTypeClassFilterMixin,
    ETypeClassFilterMixin,
    BrainRegionFilterMixin,
):
    validation_status: ValidationStatus | None = None

    morphology: Annotated[MorphologyFilter | None, NestedMorphologyFilterDep] = None
    emodel: Annotated[EModelFilter | None, NestedEModelFilterDep] = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = MEModel
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


# Dependencies
MEModelFilterDep = Annotated[MEModelFilter, FilterDepends(MEModelFilter)]
# Nested dependencies
NestedMEModelFilterDep = FilterDepends(with_prefix("me_model", MEModelFilter))
