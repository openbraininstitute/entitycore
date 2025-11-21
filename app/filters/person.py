import uuid
from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import Person
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import NestedAgentFilter


class NestedPersonFilter(NestedAgentFilter):
    given_name: str | None = None
    given_name__ilike: str | None = None
    family_name: str | None = None
    family_name__ilike: str | None = None
    sub_id: uuid.UUID | None = None
    sub_id__in: list[uuid.UUID] | None = None

    class Constants(NestedAgentFilter.Constants):
        model = Person


NestedCreatedByFilterDep = FilterDepends(with_prefix("created_by", NestedPersonFilter))
NestedUpdatedByFilterDep = FilterDepends(with_prefix("updated_by", NestedPersonFilter))


class CreatorFilterMixin:
    created_by: Annotated[NestedPersonFilter | None, NestedCreatedByFilterDep] = None
    updated_by: Annotated[NestedPersonFilter | None, NestedUpdatedByFilterDep] = None


class PersonFilter(NestedPersonFilter, CreatorFilterMixin, CustomFilter):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(NestedPersonFilter.Constants):
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "pref_label",
            "given_name",
            "family_name",
        ]


PersonFilterDep = Annotated[PersonFilter, FilterDepends(PersonFilter)]
