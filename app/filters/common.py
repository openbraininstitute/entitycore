import uuid
from datetime import datetime
from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import (
    Agent,
    ETypeClass,
    MTypeClass,
)
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter


class IdFilterMixin:
    id: uuid.UUID | None = None
    id__in: list[uuid.UUID] | None = None


class AuthorizedFilterMixin:
    authorized_public: bool | None = None
    authorized_project_id: uuid.UUID | None = None


class NameFilterMixin:
    name: str | None = None
    name__in: list[str] | None = None
    name__ilike: str | None = None


class PrefLabelMixin:
    pref_label: str | None = None
    pref_label__in: list[str] | None = None
    pref_label__ilike: str | None = None


class NestedMTypeClassFilter(IdFilterMixin, PrefLabelMixin, CustomFilter):
    class Constants(CustomFilter.Constants):
        model = MTypeClass


class MTypeClassFilter(NestedMTypeClassFilter):
    order_by: list[str] = ["pref_label"]  # noqa: RUF012

    class Constants(NestedMTypeClassFilter.Constants):
        ordering_model_fields = ["pref_label"]  # noqa: RUF012


class NestedETypeClassFilter(IdFilterMixin, PrefLabelMixin, CustomFilter):
    class Constants(CustomFilter.Constants):
        model = ETypeClass


class ETypeClassFilter(NestedETypeClassFilter):
    order_by: list[str] = ["pref_label"]  # noqa: RUF012

    class Constants(NestedETypeClassFilter.Constants):
        ordering_model_fields = ["pref_label"]  # noqa: RUF012


class NestedAgentFilter(IdFilterMixin, PrefLabelMixin, CustomFilter):
    class Constants(CustomFilter.Constants):
        model = Agent


class AgentFilter(NestedAgentFilter):
    order_by: list[str] = ["pref_label"]  # noqa: RUF012

    class Constants(NestedAgentFilter.Constants):
        ordering_model_fields = ["pref_label"]  # noqa: RUF012


class CreationFilterMixin:
    creation_date__lte: datetime | None = None
    creation_date__gte: datetime | None = None
    update_date__lte: datetime | None = None
    update_date__gte: datetime | None = None


# Dependencies
MTypeClassFilterDep = Annotated[MTypeClassFilter, FilterDepends(MTypeClassFilter)]
ETypeClassFilterDep = Annotated[ETypeClassFilter, FilterDepends(ETypeClassFilter)]
AgentFilterDep = Annotated[AgentFilter, FilterDepends(AgentFilter)]

# Nested dependencies
NestedMTypeClassFilterDep = FilterDepends(with_prefix("mtype", NestedMTypeClassFilter))
NestedETypeClassFilterDep = FilterDepends(with_prefix("etype", NestedETypeClassFilter))
NestedAgentFilterDep = FilterDepends(with_prefix("agent", NestedAgentFilter))


class MTypeClassFilterMixin:
    mtype: Annotated[NestedMTypeClassFilter | None, NestedMTypeClassFilterDep] = None


class ETypeClassFilterMixin:
    etype: Annotated[NestedETypeClassFilter | None, NestedETypeClassFilterDep] = None
