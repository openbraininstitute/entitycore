from datetime import datetime
from typing import Annotated

from app.filters.common import (
    CreationFilterMixin,
    CreatorFilterMixin,
    IdFilterMixin,
    NestedEntityFilter,
    NestedEntityFilterDep,
)


class ActivityFilterMixin(IdFilterMixin, CreatorFilterMixin, CreationFilterMixin):
    start_time: datetime | None = None
    end_time: datetime | None = None

    used: Annotated[NestedEntityFilter | None, NestedEntityFilterDep] = None
    generated: Annotated[NestedEntityFilter | None, NestedEntityFilterDep] = None
