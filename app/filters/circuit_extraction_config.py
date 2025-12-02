import uuid
from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import CircuitExtractionConfig
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.circuit import NestedCircuitFilter, NestedCircuitFilterDep
from app.filters.common import IdFilterMixin, ILikeSearchFilterMixin, NameFilterMixin
from app.filters.entity import EntityFilterMixin


class CircuitExtractionConfigFilterBase(NameFilterMixin, IdFilterMixin, CustomFilter):
    circuit_id: uuid.UUID | None = None
    circuit_id__in: list[uuid.UUID] | None = None


class NestedCircuitExtractionConfigFilter(CircuitExtractionConfigFilterBase):
    class Constants(CustomFilter.Constants):
        model = CircuitExtractionConfig


class CircuitExtractionConfigFilter(
    EntityFilterMixin, CircuitExtractionConfigFilterBase, ILikeSearchFilterMixin
):
    circuit_extraction_campaign_id: uuid.UUID | None = None
    circuit_extraction_campaign_id__in: list[uuid.UUID] | None = None

    circuit: Annotated[NestedCircuitFilter | None, NestedCircuitFilterDep] = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = CircuitExtractionConfig
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


CircuitExtractionConfigFilterDep = Annotated[
    CircuitExtractionConfigFilter, FilterDepends(CircuitExtractionConfigFilter)
]
NestedCircuitExtractionConfigFilterDep = FilterDepends(
    with_prefix("circuit_extraction_config", NestedCircuitExtractionConfigFilter)
)
