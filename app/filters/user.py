from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import User
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import IdFilterMixin, PrefLabelMixin


class NestedUserFilter(IdFilterMixin, PrefLabelMixin, CustomFilter):
    given_name: str | None = None
    given_name__ilike: str | None = None
    family_name: str | None = None
    family_name__ilike: str | None = None

    class Constants(CustomFilter.Constants):
        model = User


NestedCreatedByFilterDep = FilterDepends(with_prefix("created_by", NestedUserFilter))
NestedUpdatedByFilterDep = FilterDepends(with_prefix("updated_by", NestedUserFilter))


class CreatorFilterMixin:
    created_by: Annotated[NestedUserFilter | None, NestedCreatedByFilterDep] = None
    updated_by: Annotated[NestedUserFilter | None, NestedUpdatedByFilterDep] = None
