import uuid
from typing import Annotated, Literal

from fastapi_filter import with_prefix

from app.db.model import Entity, SimulationCampaign
from app.db.types import EntityType
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.circuit import NestedCircuitFilter, NestedCircuitFilterDep
from app.filters.common import IdFilterMixin, NameFilterMixin
from app.filters.entity import EntityFilterMixin
from app.filters.simulation import NestedSimulationFilter


class NestedEntityFilter(IdFilterMixin, CustomFilter):
    type: Literal[EntityType.circuit, EntityType.memodel] | None = None

    class Constants(CustomFilter.Constants):
        model = Entity


class SimulationCampaignFilter(CustomFilter, EntityFilterMixin, NameFilterMixin):
    entity_id: uuid.UUID | None = None
    entity_id__in: list[uuid.UUID] | None = None

    entity: Annotated[
        NestedEntityFilter | None,
        FilterDepends(with_prefix("entity", NestedEntityFilter)),
    ] = None

    circuit: Annotated[
        NestedCircuitFilter | None,
        NestedCircuitFilterDep,
    ] = None

    simulation: Annotated[
        NestedSimulationFilter | None,
        FilterDepends(with_prefix("simulation", NestedSimulationFilter)),
    ] = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = SimulationCampaign
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


SimulationCampaignFilterDep = Annotated[
    SimulationCampaignFilter, FilterDepends(SimulationCampaignFilter)
]
