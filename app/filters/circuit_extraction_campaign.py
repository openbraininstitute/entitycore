from typing import Annotated

from app.db.model import CircuitExtractionCampaign
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import NameFilterMixin
from app.filters.entity import EntityFilterMixin


class CircuitExtractionCampaignFilter(CustomFilter, EntityFilterMixin, NameFilterMixin):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = CircuitExtractionCampaign
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


CircuitExtractionCampaignFilterDep = Annotated[
    CircuitExtractionCampaignFilter, FilterDepends(CircuitExtractionCampaignFilter)
]
