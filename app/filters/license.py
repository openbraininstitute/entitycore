from typing import Annotated

from app.db.model import License
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter


class LicenseFilter(CustomFilter):
    name: str | None = None
    label: str | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = License
        ordering_model_fields = ["creation_date"]  # noqa: RUF012


LicenseFilterDep = Annotated[LicenseFilter, FilterDepends(LicenseFilter)]
