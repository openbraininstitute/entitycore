from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import Person, User
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import IdFilterMixin, PrefLabelMixin
from app.utils.pydantic_validators import ORCID


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


class NestedPersonFilter(IdFilterMixin, PrefLabelMixin, CustomFilter):
    given_name: str | None = None
    given_name__ilike: str | None = None
    family_name: str | None = None
    family_name__ilike: str | None = None
    orcid: ORCID | None = None
    orcid__in: list[ORCID] | None = None

    class Constants(CustomFilter.Constants):
        model = Person


class PersonFilter(NestedPersonFilter, CreatorFilterMixin, CustomFilter):
    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(NestedPersonFilter.Constants):
        ordering_model_fields = [  # ruff:ignore[mutable-class-default]
            "creation_date",
            "update_date",
            "pref_label",
            "given_name",
            "family_name",
        ]


PersonFilterDep = Annotated[PersonFilter, FilterDepends(PersonFilter)]
