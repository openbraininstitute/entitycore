from typing import Annotated

from app.db.model import Organization
from app.dependencies.filter import FilterDepends
from app.filters.common import AgentFilter
from app.filters.person import CreatorFilterMixin
from app.utils.pydantic_validators import ROR_ID


class OrganizationFilter(AgentFilter, CreatorFilterMixin):
    alternative_name: str | None = None

    ror_id: ROR_ID | None = None
    ror_id__in: list[ROR_ID] | None = None

    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(AgentFilter.Constants):
        model = Organization
        ordering_model_fields = [  # ruff:ignore[mutable-class-default]
            "creation_date",
            "update_date",
            "pref_label",
            "alternative_name",
        ]


OrganizationFilterDep = Annotated[OrganizationFilter, FilterDepends(OrganizationFilter)]
