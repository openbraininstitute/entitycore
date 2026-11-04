import uuid

from fastapi import Query
from pydantic import Field
from sqlalchemy import Select

from app.db.model import PlatformUser
from app.filters.base import CustomFilter
from app.filters.common import IdFilterMixin, PrefLabelMixin
from app.queries.alias_registry import Aliases


class NestedPlatformUserFilter(IdFilterMixin, PrefLabelMixin, CustomFilter):
    sub_id: uuid.UUID | None = Field(Query(None, deprecated=True))
    sub_id__in: list[uuid.UUID] | None = Field(Query(None, deprecated=True))

    class Constants(CustomFilter.Constants):
        model = PlatformUser

    def filter(self, query: Select, aliases: Aliases | None = None, **kwargs) -> Select:
        """Remap deprecated sub_id/sub_id__in to id/id__in for backward compatibility."""
        if self.sub_id is not None and self.id is None:
            self.id = self.sub_id
        if self.sub_id__in is not None and self.id__in is None:
            self.id__in = self.sub_id__in
        self.sub_id = None
        self.sub_id__in = None
        return super().filter(query, aliases, **kwargs)


class CreatorFilterMixin:
    created_by: NestedPlatformUserFilter | None = None
    updated_by: NestedPlatformUserFilter | None = None
