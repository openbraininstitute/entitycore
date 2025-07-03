import uuid
from datetime import datetime
from typing import Annotated

from app.db.model import Circuit
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    BrainRegionFilterMixin,
    EntityFilterMixin,
    NameFilterMixin,
    SubjectFilterMixin,
)


class ScientificArtifactFilter(
    CustomFilter, SubjectFilterMixin, BrainRegionFilterMixin, EntityFilterMixin
):
    experiment_date__lte: datetime | None = None
    experiment_date__gte: datetime | None = None
    contact_id: uuid.UUID | None = None


class CircuitFilter(ScientificArtifactFilter, NameFilterMixin):
    atlas_id: uuid.UUID | None = None
    root_circuit_id: uuid.UUID | None = None

    has_morphologies: bool | None = None
    has_point_neurons: bool | None = None
    has_electrical_cell_models: bool | None = None
    has_spines: bool | None = None

    number_neurons__lte: int | None = None
    number_neurons__gte: int | None = None

    number_synapses__lte: int | None = None
    number_synapses__gte: int | None = None

    number_connections__lte: int | None = None
    number_connections__gte: int | None = None

    build_category: str | None = None
    build_category__in: list[str] | None = None

    scale: str | None = None
    scale__in: list[str] | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Circuit
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


CircuitFilterDep = Annotated[CircuitFilter, FilterDepends(CircuitFilter)]
