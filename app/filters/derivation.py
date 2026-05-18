from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import Derivation
from app.db.types import DerivationType
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    CreationFilterMixin,
    IdFilterMixin,
)
from app.filters.entity import NestedEntityFilter
from app.filters.person import CreatorFilterMixin

NestedUsedFilterDep = FilterDepends(with_prefix("used", NestedEntityFilter))
NestedGeneratedFilterDep = FilterDepends(with_prefix("generated", NestedEntityFilter))


class DerivationFilter(IdFilterMixin, CreationFilterMixin, CreatorFilterMixin, CustomFilter):
    used: Annotated[NestedEntityFilter | None, NestedUsedFilterDep] = None
    generated: Annotated[NestedEntityFilter | None, NestedGeneratedFilterDep] = None
    derivation_type: DerivationType | None = None
    label: str | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Derivation
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "derivation_type",
            "label",
            "used__id",
            "generated__id",
        ]


DerivationFilterDep = Annotated[DerivationFilter, FilterDepends(DerivationFilter)]
