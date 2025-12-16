from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import Agent, Contribution
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    CreationFilterMixin,
    IdFilterMixin,
    PrefLabelMixin,
)
from app.filters.entity import NestedEntityFilter, NestedEntityFilterDep
from app.filters.person import CreatorFilterMixin


class NestedAgentFilter(IdFilterMixin, PrefLabelMixin, CustomFilter):
    class Constants(CustomFilter.Constants):
        model = Agent


NestedContributionFilter = NestedAgentFilter
NestedContributionFilterDep = FilterDepends(with_prefix("contribution", NestedAgentFilter))
NestedAgentFilterDep = FilterDepends(with_prefix("agent", NestedContributionFilter))


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
