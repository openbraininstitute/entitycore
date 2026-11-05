import uuid
from typing import Annotated, Literal

from app.db.model import Entity, SimulationCampaign
from app.db.types import EntityType
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.circuit import NestedCircuitFilter
from app.filters.common import IdFilterMixin, ILikeSearchFilterMixin, NameFilterMixin
from app.filters.entity import EntityFilterMixin
from app.filters.simulation import NestedSimulationFilter


class NestedEntityFilter(IdFilterMixin, CustomFilter):
    type: Literal[EntityType.circuit, EntityType.memodel, EntityType.ion_channel_model] | None = (
        None
    )

    class Constants(CustomFilter.Constants):
        model = Entity


class SimulationCampaignFilter(
    CustomFilter, EntityFilterMixin, NameFilterMixin, ILikeSearchFilterMixin
):
    entity_id: uuid.UUID | None = None
    entity_id__in: list[uuid.UUID] | None = None

    entity: NestedEntityFilter | None = None

    circuit: NestedCircuitFilter | None = None

    simulation: NestedSimulationFilter | None = None

    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = SimulationCampaign
        ordering_model_fields = [  # ruff:ignore[mutable-class-default]
            "id",
            "creation_date",
            "update_date",
            "name",
            "circuit__name",
            "simulation__name",
            "created_by__pref_label",
            "updated_by__pref_label",
            "contribution__pref_label",
        ]


SimulationCampaignFilterDep = Annotated[
    SimulationCampaignFilter, FilterDepends(SimulationCampaignFilter)
]
