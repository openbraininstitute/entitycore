from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import Contribution
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    CreationFilterMixin,
    IdFilterMixin,
    NestedAgentFilter,
    NestedAgentFilterDep,
)
from app.filters.entity import NestedEntityFilter, NestedEntityFilterDep
from app.filters.person import CreatorFilterMixin

NestedContributionFilter = NestedAgentFilter
NestedContributionFilterDep = FilterDepends(with_prefix("contribution", NestedAgentFilter))


class ContributionFilter(IdFilterMixin, CreationFilterMixin, CreatorFilterMixin, CustomFilter):
    agent: Annotated[NestedAgentFilter | None, NestedAgentFilterDep] = None
    entity: Annotated[NestedEntityFilter | None, NestedEntityFilterDep] = None
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Contribution
        ordering_model_fields = ["creation_date"]  # noqa: RUF012


ContributionFilterDep = Annotated[ContributionFilter, FilterDepends(ContributionFilter)]


class ContributionFilterMixin:
    contribution: Annotated[NestedContributionFilter | None, NestedContributionFilterDep] = None
