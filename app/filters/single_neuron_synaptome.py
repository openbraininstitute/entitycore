from fastapi_filter import FilterDepends, with_prefix

from app.db.model import SingleNeuronSynaptome
from app.filters.base import CustomFilter
from app.filters.common import ContributionFilterMixin, CreationFilterMixin


class MEModelFilter(CustomFilter):
    # TODO: Replace this with actual filter when merged
    id: int | None = None


class SingleNeuronSynaptomeFilter(
    CustomFilter,
    CreationFilterMixin,
    ContributionFilterMixin,
):
    name__ilike: str | None = None
    brain_region_id: int | None = None

    me_model: MEModelFilter | None = FilterDepends(with_prefix("me_type", MEModelFilter))

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = SingleNeuronSynaptome
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012
