from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import MEModel, ValidationStatus
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.brain_region import BrainRegionFilterMixin, NestedBrainRegionFilter
from app.filters.cell_morphology import NestedCellMorphologyFilter
from app.filters.common import (
    ETypeClassFilterMixin,
    IdFilterMixin,
    MTypeClassFilterMixin,
    NameFilterMixin,
    NestedETypeClassFilter,
    NestedMTypeClassFilter,
)
from app.filters.emodel import NestedEModelFilter
from app.filters.entity import EntityFilterMixin
from app.filters.species import NestedSpeciesFilter, NestedStrainFilter, SpeciesFilterMixin


class NestedMEModelFilter(
    IdFilterMixin,
    NameFilterMixin,
    CustomFilter,
):
    validation_status: ValidationStatus | None = None

    brain_region: Annotated[
        NestedBrainRegionFilter | None,
        FilterDepends(with_prefix("me_model__brain_region", NestedBrainRegionFilter)),
    ] = None
    species: Annotated[
        NestedSpeciesFilter | None,
        FilterDepends(with_prefix("me_model__species", NestedSpeciesFilter)),
    ] = None
    strain: Annotated[
        NestedStrainFilter | None,
        FilterDepends(with_prefix("me_model__strain", NestedStrainFilter)),
    ] = None
    morphology: Annotated[
        NestedCellMorphologyFilter | None,
        FilterDepends(with_prefix("me_model__morphology", NestedCellMorphologyFilter)),
    ] = None
    emodel: Annotated[
        NestedEModelFilter | None,
        FilterDepends(with_prefix("me_model__emodel", NestedEModelFilter)),
    ] = None
    mtype: Annotated[
        NestedMTypeClassFilter | None,
        FilterDepends(with_prefix("me_model__mtype", NestedMTypeClassFilter)),
    ] = None
    etype: Annotated[
        NestedETypeClassFilter | None,
        FilterDepends(with_prefix("me_model__etype", NestedETypeClassFilter)),
    ] = None

    class Constants(CustomFilter.Constants):
        model = MEModel


class MEModelFilter(
    EntityFilterMixin,
    NameFilterMixin,
    SpeciesFilterMixin,
    MTypeClassFilterMixin,
    ETypeClassFilterMixin,
    BrainRegionFilterMixin,
    CustomFilter,
):
    morphology: Annotated[
        NestedCellMorphologyFilter | None,
        FilterDepends(with_prefix("morphology", NestedCellMorphologyFilter)),
    ] = None
    emodel: Annotated[
        NestedEModelFilter | None,
        FilterDepends(with_prefix("emodel", NestedEModelFilter)),
    ] = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = MEModel
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "brain_region__name",
            "brain_region__acronym",
            "created_by__pref_label",
            "name",
        ]


# Dependencies
MEModelFilterDep = Annotated[MEModelFilter, FilterDepends(MEModelFilter)]
# Nested dependencies
NestedMEModelFilterDep = FilterDepends(with_prefix("me_model", NestedMEModelFilter))
