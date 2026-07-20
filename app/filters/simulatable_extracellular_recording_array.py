from typing import Annotated
from uuid import UUID

from app.db.model import SimulatableExtracellularRecordingArray
from app.db.types import ElectrodeType
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    ILikeSearchFilterMixin,
    NameFilterMixin,
)
from app.filters.entity import EntityFilterMixin


class SimulatableExtracellularRecordingArrayFilter(
    NameFilterMixin,
    EntityFilterMixin,
    ILikeSearchFilterMixin,
    CustomFilter,
):
    electrode_type: ElectrodeType | None = None
    circuit_id: UUID | None = None

    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = SimulatableExtracellularRecordingArray
        ordering_model_fields = ["creation_date", "update_date", "name"]  # ruff:ignore[mutable-class-default]


SimulatableExtracellularRecordingArrayFilterDep = Annotated[
    SimulatableExtracellularRecordingArrayFilter,
    FilterDepends(SimulatableExtracellularRecordingArrayFilter),
]
