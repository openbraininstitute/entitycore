from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import CellMorphology
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.cell_morphology_protocol import (
    NestedCellMorphologyProtocolFilter,
    NestedCellMorphologyProtocolFilterDep,
)
from app.filters.common import (
    BrainRegionFilterMixin,
    EntityFilterMixin,
    IdFilterMixin,
    MTypeClassFilterMixin,
    NameFilterMixin,
    NestedBrainRegionFilter,
    NestedMTypeClassFilter,
)
from app.filters.measurement_annotation import MeasurableFilterMixin
from app.filters.subject import NestedSubjectFilter, SubjectFilterMixin


class NestedCellMorphologyFilter(
    IdFilterMixin,
    NameFilterMixin,
    CustomFilter,
):
    brain_region: Annotated[
        NestedBrainRegionFilter | None,
        FilterDepends(with_prefix("morphology__brain_region", NestedBrainRegionFilter)),
    ] = None
    subject: Annotated[
        NestedSubjectFilter | None,
        FilterDepends(with_prefix("morphology__subject", NestedSubjectFilter)),
    ] = None
    mtype: Annotated[
        NestedMTypeClassFilter | None,
        FilterDepends(with_prefix("morphology__mtype", NestedMTypeClassFilter)),
    ] = None

    class Constants(CustomFilter.Constants):
        model = CellMorphology


class NestedExemplarMorphologyFilter(
    IdFilterMixin,
    NameFilterMixin,
    CustomFilter,
):
    brain_region: Annotated[
        NestedBrainRegionFilter | None,
        FilterDepends(with_prefix("exemplar_morphology__brain_region", NestedBrainRegionFilter)),
    ] = None
    subject: Annotated[
        NestedSubjectFilter | None,
        FilterDepends(with_prefix("exemplar_morphology__subject", NestedSubjectFilter)),
    ] = None
    mtype: Annotated[
        NestedMTypeClassFilter | None,
        FilterDepends(with_prefix("exemplar_morphology__mtype", NestedMTypeClassFilter)),
    ] = None

    class Constants(CustomFilter.Constants):
        model = CellMorphology


class CellMorphologyFilter(
    EntityFilterMixin,
    BrainRegionFilterMixin,
    SubjectFilterMixin,
    MTypeClassFilterMixin,
    MeasurableFilterMixin,
    NameFilterMixin,
    CustomFilter,
):
    cell_morphology_protocol: Annotated[
        NestedCellMorphologyProtocolFilter | None, NestedCellMorphologyProtocolFilterDep
    ] = None
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = CellMorphology
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "name",
            "brain_region__name",
            "brain_region__acronym",
            "mtype__pref_label",
        ]


# Dependencies
CellMorphologyFilterDep = Annotated[CellMorphologyFilter, FilterDepends(CellMorphologyFilter)]
