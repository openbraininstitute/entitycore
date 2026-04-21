from typing import Annotated

from app.db.model import CellMorphology
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.brain_region import BrainRegionFilterMixin
from app.filters.cell_morphology_protocol import (
    NestedCellMorphologyProtocolFilter,
    NestedCellMorphologyProtocolFilterDep,
)
from app.filters.common import (
    IdFilterMixin,
    ILikeSearchFilterMixin,
    MTypeClassFilterMixin,
    NameFilterMixin,
)
from app.filters.entity import EntityFilterMixin
from app.filters.measurement_annotation import MeasurableFilterMixin
from app.filters.subject import SubjectFilterMixin


class CellMorphologyFilterBase(
    IdFilterMixin,
    NameFilterMixin,
    CustomFilter,
):
    has_segmented_spines: bool | None = None

    class Constants(CustomFilter.Constants):
        model = CellMorphology


class NestedCellMorphologyFilter(
    CellMorphologyFilterBase,
):
    pass


class CellMorphologyFilter(
    EntityFilterMixin,
    BrainRegionFilterMixin,
    SubjectFilterMixin,
    MTypeClassFilterMixin,
    MeasurableFilterMixin,
    ILikeSearchFilterMixin,
    CellMorphologyFilterBase,
):
    cell_morphology_protocol: Annotated[
        NestedCellMorphologyProtocolFilter | None, NestedCellMorphologyProtocolFilterDep
    ] = None
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CellMorphologyFilterBase.Constants):
        ordering_model_fields = [  # noqa: RUF012
            "id",
            "creation_date",
            "update_date",
            "name",
            "has_segmented_spines",
            "brain_region__name",
            "brain_region__acronym",
            "mtype__pref_label",
            "subject__name",
            "subject__species__name",
            "subject__strain__name",
            "cell_morphology_protocol__name",
            "created_by__pref_label",
            "updated_by__pref_label",
            "cell_morphology_protocol__generation_type",
        ]


# Dependencies
CellMorphologyFilterDep = Annotated[CellMorphologyFilter, FilterDepends(CellMorphologyFilter)]
