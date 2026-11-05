from typing import Annotated

from app.db.model import Derivation
from app.db.types import DerivationType
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    CreationFilterMixin,
    IdFilterMixin,
)
from app.filters.entity import NestedEntityFilter
from app.filters.platform_user import CreatorFilterMixin


class DerivationFilter(IdFilterMixin, CreationFilterMixin, CreatorFilterMixin, CustomFilter):
    used: NestedEntityFilter | None = None
    generated: NestedEntityFilter | None = None
    derivation_type: DerivationType | None = None
    label: str | None = None

    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = Derivation
        ordering_model_fields = [  # ruff:ignore[mutable-class-default]
            "creation_date",
            "derivation_type",
            "label",
            "used__id",
            "generated__id",
        ]


DerivationFilterDep = Annotated[DerivationFilter, FilterDepends(DerivationFilter)]
