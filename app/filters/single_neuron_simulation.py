from fastapi_filter import FilterDepends, with_prefix

from app.db.model import SingleNeuronSimulation
from app.db.types import SingleNeuronSimulationStatus
from app.filters.base import CustomFilter
from app.filters.common import ContributionFilterMixin, CreationFilterMixin
from app.filters.memodel import MEModelFilter


class SingleNeuronSimulationFilter(
    CustomFilter,
    CreationFilterMixin,
    ContributionFilterMixin,
):
    name__ilike: str | None = None
    brain_region_id: int | None = None
    status: SingleNeuronSimulationStatus | None = None

    me_model: MEModelFilter | None = FilterDepends(with_prefix("me_type", MEModelFilter))

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = SingleNeuronSimulation
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012
