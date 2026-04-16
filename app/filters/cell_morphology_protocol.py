from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import CellMorphologyProtocol
from app.db.types import CellMorphologyGenerationType, CellMorphologyProtocolDesign
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import IdFilterMixin, ILikeSearchFilterMixin, NameFilterMixin
from app.filters.entity import EntityFilterMixin


class CellMorphologyProtocolFilterBase(
    IdFilterMixin,
    NameFilterMixin,
    CustomFilter,
):
    generation_type: CellMorphologyGenerationType | None = None
    generation_type__in: list[CellMorphologyGenerationType] | None = None
    generation_type__not_in: list[CellMorphologyGenerationType] | None = None

    protocol_design: CellMorphologyProtocolDesign | None = None
    protocol_design__in: list[CellMorphologyProtocolDesign] | None = None
    protocol_design__not_in: list[CellMorphologyProtocolDesign] | None = None

    protocol_document: str | None = None
    protocol_document__in: list[str] | None = None
    protocol_document__ilike: str | None = None

    class Constants(CustomFilter.Constants):
        model = CellMorphologyProtocol


class NestedCellMorphologyProtocolFilter(
    CellMorphologyProtocolFilterBase,
):
    pass


class CellMorphologyProtocolFilter(
    EntityFilterMixin,
    CellMorphologyProtocolFilterBase,
    ILikeSearchFilterMixin,
):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CellMorphologyProtocolFilterBase.Constants):
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "generation_type",
        ]


# Dependencies
CellMorphologyProtocolFilterDep = Annotated[
    CellMorphologyProtocolFilter, FilterDepends(CellMorphologyProtocolFilter)
]

# Nested dependencies
NestedCellMorphologyProtocolFilterDep = FilterDepends(
    with_prefix("cell_morphology_protocol", NestedCellMorphologyProtocolFilter)
)
