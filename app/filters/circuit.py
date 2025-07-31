import uuid
from typing import Annotated

from app.db.model import Circuit
from app.dependencies.filter import FilterDepends
from app.filters.common import NameFilterMixin
from app.filters.scientific_artifact import ScientificArtifactFilter


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

    class Constants(ScientificArtifactFilter.Constants):
        model = Circuit
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


CircuitFilterDep = Annotated[CircuitFilter, FilterDepends(CircuitFilter)]
