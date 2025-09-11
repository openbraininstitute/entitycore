import uuid
from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import Circuit
from app.db.types import CircuitBuildCategory, CircuitScale
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import IdFilterMixin, NameFilterMixin
from app.filters.scientific_artifact import ScientificArtifactFilter


class CircuitFilterMixin:
    scale: CircuitScale | None = None
    scale__in: list[CircuitScale] | None = None

    build_category: CircuitBuildCategory | None = None
    build_category__in: list[CircuitBuildCategory] | None = None


class NestedCircuitFilter(
    IdFilterMixin,
    NameFilterMixin,
    CircuitFilterMixin,
    CustomFilter,
):
    """Circuit filter with limited fields for nesting."""

    class Constants(CustomFilter.Constants):
        model = Circuit


class CircuitFilter(
    ScientificArtifactFilter,
    NameFilterMixin,
    CircuitFilterMixin,
):
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

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(ScientificArtifactFilter.Constants):
        model = Circuit
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


CircuitFilterDep = Annotated[CircuitFilter, FilterDepends(CircuitFilter)]
NestedCircuitFilterDep = FilterDepends(with_prefix("circuit", NestedCircuitFilter))
