from typing import Annotated

from app.db.model import MEModel
from app.db.types import ValidationStatus
from app.filters.base import CustomFilter, Prefix
from app.filters.brain_region import BrainRegionFilterMixin
from app.filters.cell_morphology import NestedCellMorphologyFilter
from app.filters.common import (
    ETypeClassFilterMixin,
    IdFilterMixin,
    ILikeSearchFilterMixin,
    MTypeClassFilterMixin,
    NameFilterMixin,
    NestedETypeClassFilter,
    NestedMTypeClassFilter,
)
from app.filters.emodel import NestedEModelFilter
from app.filters.entity import EntityFilterMixin, NestedDerivationFilter
from app.filters.species import NestedSpeciesFilter, SpeciesFilterMixin


class NestedMEModelMorphologyFilter(NestedCellMorphologyFilter):
    generated_derivation: Annotated[
        NestedDerivationFilter | None, Prefix(value="morphology__generated_derivation")
    ] = None


class NestedMEModelFilter(
    IdFilterMixin,
    NameFilterMixin,
    CustomFilter,
):
    validation_status: ValidationStatus | None = None

    species: Annotated[NestedSpeciesFilter | None, Prefix(value="me_model__species")] = None
    mtype: Annotated[NestedMTypeClassFilter | None, Prefix(value="me_model__mtype")] = None
    etype: Annotated[NestedETypeClassFilter | None, Prefix(value="me_model__etype")] = None

    class Constants(CustomFilter.Constants):
        model = MEModel


class MEModelFilter(
    EntityFilterMixin,
    NameFilterMixin,
    SpeciesFilterMixin,
    MTypeClassFilterMixin,
    ETypeClassFilterMixin,
    BrainRegionFilterMixin,
    ILikeSearchFilterMixin,
    CustomFilter,
):
    morphology: NestedMEModelMorphologyFilter | None = None
    emodel: NestedEModelFilter | None = None

    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = MEModel
        ordering_model_fields = [  # ruff:ignore[mutable-class-default]
            "creation_date",
            "update_date",
            "brain_region__name",
            "brain_region__acronym",
            "created_by__pref_label",
            "name",
            "mtype__pref_label",
            "etype__pref_label",
        ]
