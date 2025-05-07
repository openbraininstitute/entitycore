from typing import Annotated

from fastapi_filter import FilterDepends

from app.db.model import Label
from app.db.types import LabelScheme
from app.filters.base import CustomFilter
from app.filters.common import CreationFilterMixin


class LabelFilter(
    CustomFilter,
    CreationFilterMixin,
):
    scheme: LabelScheme | None = None
    pref_label: str | None = None
    pref_label__ilike: str | None = None

    order_by: list[str] = ["pref_label"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Label
        ordering_model_fields = ["creation_date", "update_date", "pref_label"]  # noqa: RUF012


LabelFilterDep = Annotated[LabelFilter, FilterDepends(LabelFilter)]
