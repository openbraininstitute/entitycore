from typing import Annotated

from fastapi_filter import FilterDepends

from app.db.model import SingleNeuronSynaptome
from app.filters.base import CustomFilter, with_nested_prefix
from app.filters.common import (
    BrainRegionFilterMixin,
    EntityFilterMixin,
    NameFilterMixin,
)
from app.filters.memodel import MEModelFilter, NestedMEModelFilterDep


class SingleNeuronSynaptomeFilter(
    CustomFilter,
    BrainRegionFilterMixin,
    EntityFilterMixin,
    NameFilterMixin,
):
    me_model: Annotated[MEModelFilter | None, NestedMEModelFilterDep] = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = SingleNeuronSynaptome
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


# Dependencies
SingleNeuronSynaptomeFilterDep = Annotated[
    SingleNeuronSynaptomeFilter, FilterDepends(SingleNeuronSynaptomeFilter)
]
# Nested dependencies
NestedSingleNeuronSynaptomeFilterDep = FilterDepends(
    with_nested_prefix("synaptome", SingleNeuronSynaptomeFilter)
)
