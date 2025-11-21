from typing import Annotated

from app.db.model import Organization
from app.dependencies.filter import FilterDepends
from app.filters.common import AgentFilter
from app.filters.person import CreatorFilterMixin


class OrganizationFilter(AgentFilter, CreatorFilterMixin):
    alternative_name: str | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(AgentFilter.Constants):
        model = Organization
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "pref_label",
            "alternative_name",
        ]


OrganizationFilterDep = Annotated[OrganizationFilter, FilterDepends(OrganizationFilter)]
