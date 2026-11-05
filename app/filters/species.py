from app.db.model import Species, Strain
from app.filters.base import CustomFilter
from app.filters.common import CreationFilterMixin, IdFilterMixin, NameFilterMixin
from app.filters.platform_user import CreatorFilterMixin


class NestedSpeciesFilter(IdFilterMixin, NameFilterMixin, CustomFilter):
    """Species filter with limited fields for nesting."""

    class Constants(CustomFilter.Constants):
        model = Species


class SpeciesFilter(CreationFilterMixin, CreatorFilterMixin, NestedSpeciesFilter):
    """Full species filter."""

    order_by: list[str] = ["name"]  # ruff:ignore[mutable-class-default]

    class Constants(NestedSpeciesFilter.Constants):
        ordering_model_fields = ["name"]  # ruff:ignore[mutable-class-default]


class NestedStrainFilter(IdFilterMixin, NameFilterMixin, CustomFilter):
    class Constants(CustomFilter.Constants):
        model = Strain


class StrainFilter(CreationFilterMixin, CreatorFilterMixin, NestedStrainFilter):
    """Full strain filter."""

    order_by: list[str] = ["name"]  # ruff:ignore[mutable-class-default]

    class Constants(NestedStrainFilter.Constants):
        ordering_model_fields = ["name"]  # ruff:ignore[mutable-class-default]


class SpeciesFilterMixin:
    species: NestedSpeciesFilter | None = None
    strain: NestedStrainFilter | None = None
