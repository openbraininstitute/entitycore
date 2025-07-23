from typing import Annotated

from app.db.model import Consortium
from app.dependencies.filter import FilterDepends
from app.filters.common import AgentFilter, CreatorFilterMixin


class ConsortiumFilter(AgentFilter, CreatorFilterMixin):
    alternative_name: str | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(AgentFilter.Constants):
        model = Consortium
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "pref_label",
            "alternative_name",
        ]


ConsortiumFilterDep = Annotated[ConsortiumFilter, FilterDepends(ConsortiumFilter)]
