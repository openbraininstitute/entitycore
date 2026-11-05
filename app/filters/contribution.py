from app.db.model import Contribution
from app.filters.base import CustomFilter
from app.filters.common import (
    CreationFilterMixin,
    IdFilterMixin,
    NestedAgentFilter,
)
from app.filters.entity import NestedEntityFilter
from app.filters.platform_user import CreatorFilterMixin

NestedContributionFilter = NestedAgentFilter


class ContributionFilter(IdFilterMixin, CreationFilterMixin, CreatorFilterMixin, CustomFilter):
    agent: NestedAgentFilter | None = None
    entity: NestedEntityFilter | None = None
    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = Contribution
        ordering_model_fields = ["creation_date"]  # ruff:ignore[mutable-class-default]


class ContributionFilterMixin:
    contribution: NestedContributionFilter | None = None
