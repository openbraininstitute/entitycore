from datetime import datetime
from typing import Annotated

from fastapi_filter import FilterDepends, with_prefix

from app.filters.common import (
    CreationFilterMixin,
    CreatorFilterMixin,
    IdFilterMixin,
    NestedEntityFilter,
)

NestedUsedFilterDep = FilterDepends(with_prefix("used", NestedEntityFilter))
NestedGeneratedFilterDep = FilterDepends(with_prefix("generated", NestedEntityFilter))


class ActivityFilterMixin(IdFilterMixin, CreatorFilterMixin, CreationFilterMixin):
    start_time: datetime | None = None
    end_time: datetime | None = None

    used: Annotated[NestedEntityFilter | None, NestedUsedFilterDep] = None
    generated: Annotated[NestedEntityFilter | None, NestedGeneratedFilterDep] = None
