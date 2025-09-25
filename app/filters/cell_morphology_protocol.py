from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import CellMorphologyProtocol
from app.db.types import CellMorphologyGenerationType
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import EntityFilterMixin, IdFilterMixin


class CellMorphologyProtocolFilterBase(
    IdFilterMixin,
    CustomFilter,
):
    generation_type: CellMorphologyGenerationType | None = None
    generation_type__in: list[CellMorphologyGenerationType] | None = None

    class Constants(CustomFilter.Constants):
        model = CellMorphologyProtocol


class NestedCellMorphologyProtocolFilter(
    CellMorphologyProtocolFilterBase,
):
    pass


class CellMorphologyProtocolFilter(
    EntityFilterMixin,
    CellMorphologyProtocolFilterBase,
):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CellMorphologyProtocolFilterBase.Constants):
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
        ]


# Dependencies
CellMorphologyProtocolFilterDep = Annotated[
    CellMorphologyProtocolFilter, FilterDepends(CellMorphologyProtocolFilter)
]

# Nested dependencies
NestedCellMorphologyProtocolFilterDep = FilterDepends(
    with_prefix("cell_morphology_protocol", NestedCellMorphologyProtocolFilter)
)
