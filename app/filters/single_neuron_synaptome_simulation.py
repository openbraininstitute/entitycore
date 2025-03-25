from fastapi_filter import FilterDepends, with_prefix

from app.db.model import SingleNeuronSynaptomeSimulation
from app.db.types import SingleNeuronSimulationStatus
from app.filters.base import CustomFilter
from app.filters.common import ContributionFilterMixin, CreationFilterMixin
from app.filters.single_neuron_synaptome import SingleNeuronSynaptomeFilter


class SingleNeuronSynaptomeSimulationFilter(
    CustomFilter,
    CreationFilterMixin,
    ContributionFilterMixin,
):
    name__ilike: str | None = None
    brain_region_id: int | None = None
    status: SingleNeuronSimulationStatus | None = None

    synaptome: SingleNeuronSynaptomeFilter | None = FilterDepends(
        with_prefix("synaptome", SingleNeuronSynaptomeFilter)
    )

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = SingleNeuronSynaptomeSimulation
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012
