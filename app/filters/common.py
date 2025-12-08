import uuid
from datetime import datetime
from typing import Annotated

from fastapi import Query
from fastapi_filter import with_prefix
from pydantic import Field

from app.db.model import (
    Agent,
    ETypeClass,
    MTypeClass,
)
from app.dependencies.filter import FilterDepends
from app.filters.base import ILIKE_SEARCH_FIELD_NAME, ILIKE_SEARCH_FIELDS, CustomFilter


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


class ILikeSearchFilterMixin:
    def __init_subclass__(cls, **kwargs):
        """Add ilike search on multiple columns.

        Ensure that this mixin is added to a filter corresponding to a model with
        ILIKE_SEARCH_FIELDS available.
        """
        # Set fastapi-filter custom search name and fields
        # See example: https://github.com/arthurio/fastapi-filter/blob/8c07dd55dfa63f09ae70eb980d51714323809906/examples/fastapi_filter_mongoengine.py#L91-L92
        cls.Constants.search_field_name = ILIKE_SEARCH_FIELD_NAME  # pyright: ignore [reportAttributeAccessIssue]

        # allow search_model_fields overrides
        if not getattr(cls.Constants, "search_model_fields", None):  # pyright: ignore [reportAttributeAccessIssue]
            # otherwise set default fields
            cls.Constants.search_model_fields = ILIKE_SEARCH_FIELDS  # pyright: ignore [reportAttributeAccessIssue]

        search_model_fields = cls.Constants.search_model_fields  # pyright: ignore [reportAttributeAccessIssue]

        # Add filter key and annotation for ilike_search
        cls.__annotations__[ILIKE_SEARCH_FIELD_NAME] = str | None

        setattr(
            cls,
            ILIKE_SEARCH_FIELD_NAME,
            Field(
                Query(
                    description=(
                        "Search text with wildcard support. Use * for zero or more characters "
                        "and ? for exactly one character. All other characters are treated as "
                        "literals. "
                        "Examples: 'test*' matches 'testing', 'file?.txt' matches 'file1.txt'. "
                        f"search_model_fields: {', '.join(search_model_fields)}"
                    ),
                    default=None,
                ),
            ),
        )


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
