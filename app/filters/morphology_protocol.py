from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import MorphologyProtocol
from app.db.types import MorphologyGenerationType
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import EntityFilterMixin, IdFilterMixin


class MorphologyProtocolFilterBase(
    IdFilterMixin,
    CustomFilter,
):
    generation_type: MorphologyGenerationType | None = None

    class Constants(CustomFilter.Constants):
        model = MorphologyProtocol


class NestedMorphologyProtocolFilter(
    MorphologyProtocolFilterBase,
):
    pass


class MorphologyProtocolFilter(
    EntityFilterMixin,
    MorphologyProtocolFilterBase,
):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(MorphologyProtocolFilterBase.Constants):
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
        ]


# Dependencies
MorphologyProtocolFilterDep = Annotated[
    MorphologyProtocolFilter, FilterDepends(MorphologyProtocolFilter)
]

# Nested dependencies
NestedMorphologyProtocolFilterDep = FilterDepends(
    with_prefix("morphology_protocol", NestedMorphologyProtocolFilter)
)
