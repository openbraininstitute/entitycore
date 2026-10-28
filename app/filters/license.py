from typing import Annotated

from app.db.model import License
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import IdFilterMixin, ILikeSearchFilterMixin, NameFilterMixin


class LicenseFilter(IdFilterMixin, NameFilterMixin, ILikeSearchFilterMixin, CustomFilter):
    label: str | None = None
    label__ilike: str | None = None

    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = License
        ordering_model_fields = ["creation_date"]  # ruff:ignore[mutable-class-default]


LicenseFilterDep = Annotated[LicenseFilter, FilterDepends(LicenseFilter)]
