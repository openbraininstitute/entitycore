import uuid
from typing import Annotated

from fastapi import Query
from fastapi_filter import with_prefix
from pydantic import Field
from sqlalchemy import Select

from app.db.model import User
from app.dependencies.filter import FilterDepends
from app.filters.base import Aliases, CustomFilter
from app.filters.common import IdFilterMixin, PrefLabelMixin


class NestedUserFilter(IdFilterMixin, PrefLabelMixin, CustomFilter):
    given_name: str | None = None
    given_name__ilike: str | None = None
    family_name: str | None = None
    family_name__ilike: str | None = None
    sub_id: uuid.UUID | None = Field(Query(None, deprecated=True))
    sub_id__in: list[uuid.UUID] | None = Field(Query(None, deprecated=True))

    class Constants(CustomFilter.Constants):
        model = User

    def filter(self, query: Select, aliases: Aliases | None = None) -> Select:
        """Remap deprecated sub_id/sub_id__in to id/id__in for backward compatibility."""
        if self.sub_id is not None and self.id is None:
            self.id = self.sub_id
        if self.sub_id__in is not None and self.id__in is None:
            self.id__in = self.sub_id__in
        self.sub_id = None
        self.sub_id__in = None
        return super().filter(query, aliases)


NestedCreatedByFilterDep = FilterDepends(with_prefix("created_by", NestedUserFilter))
NestedUpdatedByFilterDep = FilterDepends(with_prefix("updated_by", NestedUserFilter))


class CreatorFilterMixin:
    created_by: Annotated[NestedUserFilter | None, NestedCreatedByFilterDep] = None
    updated_by: Annotated[NestedUserFilter | None, NestedUpdatedByFilterDep] = None
