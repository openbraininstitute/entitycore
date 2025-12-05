from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import EModel
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.brain_region import BrainRegionFilterMixin, NestedBrainRegionFilter
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
from app.filters.entity import EntityFilterMixin
from app.filters.ion_channel_model import NestedIonChannelModelFilter
from app.filters.species import SpeciesFilterMixin


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
        NestedCellMorphologyFilter | None,
        FilterDepends(with_prefix("emodel__exemplar_morphology", NestedCellMorphologyFilter)),
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
    ILikeSearchFilterMixin,
    CustomFilter,
):
    score__lte: float | None = None
    score__gte: float | None = None

    exemplar_morphology: Annotated[
        NestedCellMorphologyFilter | None,
        FilterDepends(with_prefix("exemplar_morphology", NestedCellMorphologyFilter)),
    ] = None

    ion_channel_model: Annotated[
        NestedIonChannelModelFilter | None,
        FilterDepends(with_prefix("ion_channel_model", NestedIonChannelModelFilter)),
    ] = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = EModel
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "name",
            "brain_region__name",
            "brain_region__acronym",
            "score",
            "exemplar_morphology__name",
            "mtype__pref_label",
            "etype__pref_label",
        ]


# Dependencies
EModelFilterDep = Annotated[EModelFilter, FilterDepends(EModelFilter)]
# Nested dependencies
NestedEModelFilterDep = FilterDepends(with_prefix("emodel", NestedEModelFilter))
