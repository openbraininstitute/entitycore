from typing import Annotated

from fastapi_filter import FilterDepends, with_prefix

from app.db.model import ReconstructionMorphology
from app.filters.base import CustomFilter
from app.filters.common import (
    BrainRegionFilterMixin,
    EntityFilterMixin,
    MTypeClassFilterMixin,
    SpeciesFilterMixin,
)
from app.filters.measurement_annotation import (
    NestedMeasurementAnnotationFilter,
    NestedMeasurementAnnotationFilterDep,
)


class MorphologyFilter(
    CustomFilter,
    BrainRegionFilterMixin,
    SpeciesFilterMixin,
    MTypeClassFilterMixin,
    EntityFilterMixin,
):
    measurement_annotation: Annotated[
        NestedMeasurementAnnotationFilter | None, NestedMeasurementAnnotationFilterDep
    ] = None
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = ReconstructionMorphology
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


# Dependencies
MorphologyFilterDep = Annotated[MorphologyFilter, FilterDepends(MorphologyFilter)]
# Nested dependencies
NestedMorphologyFilterDep = FilterDepends(with_prefix("morphology", MorphologyFilter))
NestedExemplarMorphologyFilterDep = FilterDepends(
    with_prefix("exemplar_morphology", MorphologyFilter)
)
