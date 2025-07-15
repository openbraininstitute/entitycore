import uuid
from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import ReconstructionMorphology
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    BrainRegionFilterMixin,
    EntityFilterMixin,
    IdFilterMixin,
    MTypeClassFilterMixin,
    NameFilterMixin,
    NestedBrainRegionFilter,
    NestedMTypeClassFilter,
    NestedSpeciesFilter,
    NestedStrainFilter,
    SpeciesFilterMixin,
)
from app.filters.measurement_annotation import MeasurableFilterMixin


class NestedMorphologyFilter(
    IdFilterMixin,
    NameFilterMixin,
    CustomFilter,
):
    brain_region: Annotated[
        NestedBrainRegionFilter | None,
        FilterDepends(with_prefix("morphology__brain_region", NestedBrainRegionFilter)),
    ] = None
    species_id__in: list[uuid.UUID] | None = None
    species: Annotated[
        NestedSpeciesFilter | None,
        FilterDepends(with_prefix("morphology__species", NestedSpeciesFilter)),
    ] = None
    strain: Annotated[
        NestedStrainFilter | None,
        FilterDepends(with_prefix("morphology__strain", NestedStrainFilter)),
    ] = None
    mtype: Annotated[
        NestedMTypeClassFilter | None,
        FilterDepends(with_prefix("morphology__mtype", NestedMTypeClassFilter)),
    ] = None

    class Constants(CustomFilter.Constants):
        model = ReconstructionMorphology


class NestedExemplarMorphologyFilter(
    IdFilterMixin,
    NameFilterMixin,
    CustomFilter,
):
    brain_region: Annotated[
        NestedBrainRegionFilter | None,
        FilterDepends(with_prefix("exemplar_morphology__brain_region", NestedBrainRegionFilter)),
    ] = None
    species: Annotated[
        NestedSpeciesFilter | None,
        FilterDepends(with_prefix("exemplar_morphology__species", NestedSpeciesFilter)),
    ] = None
    strain: Annotated[
        NestedStrainFilter | None,
        FilterDepends(with_prefix("exemplar_morphology__strain", NestedStrainFilter)),
    ] = None
    mtype: Annotated[
        NestedMTypeClassFilter | None,
        FilterDepends(with_prefix("exemplar_morphology__mtype", NestedMTypeClassFilter)),
    ] = None

    class Constants(CustomFilter.Constants):
        model = ReconstructionMorphology


class MorphologyFilter(
    EntityFilterMixin,
    BrainRegionFilterMixin,
    SpeciesFilterMixin,
    MTypeClassFilterMixin,
    MeasurableFilterMixin,
    NameFilterMixin,
    CustomFilter,
):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = ReconstructionMorphology
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "name",
            "brain_region__name",
            "brain_region__acronym",
        ]


# Dependencies
MorphologyFilterDep = Annotated[MorphologyFilter, FilterDepends(MorphologyFilter)]

# Nested dependencies
NestedMorphologyFilterDep = FilterDepends(with_prefix("morphology", NestedMorphologyFilter))
NestedExemplarMorphologyFilterDep = FilterDepends(
    with_prefix("exemplar_morphology", NestedExemplarMorphologyFilter)
)
