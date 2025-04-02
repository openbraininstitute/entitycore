from app.db.model import ElectricalCellRecording
from app.filters.base import CustomFilter
from app.filters.common import ContributionFilterMixin, CreationFilterMixin


class ElectricalCellRecordingFilter(
    CustomFilter,
    CreationFilterMixin,
    ContributionFilterMixin,
):
    name__ilike: str | None = None
    brain_region_id: int | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = ElectricalCellRecording
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012
