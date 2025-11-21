from datetime import datetime
from typing import Annotated

from fastapi_filter import with_prefix

from app.dependencies.filter import FilterDepends
from app.filters.common import (
    CreationFilterMixin,
    IdFilterMixin,
)
from app.filters.entity import NestedEntityFilter
from app.filters.person import CreatorFilterMixin

NestedUsedFilterDep = FilterDepends(with_prefix("used", NestedEntityFilter))
NestedGeneratedFilterDep = FilterDepends(with_prefix("generated", NestedEntityFilter))


class ActivityFilterMixin(IdFilterMixin, CreatorFilterMixin, CreationFilterMixin):
    start_time: datetime | None = None
    end_time: datetime | None = None

    used: Annotated[NestedEntityFilter | None, NestedUsedFilterDep] = None
    generated: Annotated[NestedEntityFilter | None, NestedGeneratedFilterDep] = None
