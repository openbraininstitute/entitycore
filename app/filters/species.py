import uuid
from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import Species, Strain
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import CreationFilterMixin, IdFilterMixin, NameFilterMixin
from app.filters.person import CreatorFilterMixin


class NestedSpeciesFilter(IdFilterMixin, NameFilterMixin, CustomFilter):
    """Species filter with limited fields for nesting."""

    class Constants(CustomFilter.Constants):
        model = Species


class SpeciesFilter(CreationFilterMixin, CreatorFilterMixin, NestedSpeciesFilter):
    """Full species filter."""

    order_by: list[str] = ["name"]  # noqa: RUF012

    class Constants(NestedSpeciesFilter.Constants):
        ordering_model_fields = ["name"]  # noqa: RUF012


SpeciesFilterDep = Annotated[SpeciesFilter, FilterDepends(SpeciesFilter)]
NestedSpeciesFilterDep = FilterDepends(with_prefix("species", NestedSpeciesFilter))


class NestedStrainFilter(IdFilterMixin, NameFilterMixin, CustomFilter):
    class Constants(CustomFilter.Constants):
        model = Strain


class StrainFilter(CreationFilterMixin, CreatorFilterMixin, NestedStrainFilter):
    """Full strain filter."""

    order_by: list[str] = ["name"]  # noqa: RUF012

    class Constants(NestedStrainFilter.Constants):
        ordering_model_fields = ["name"]  # noqa: RUF012


StrainFilterDep = Annotated[StrainFilter, FilterDepends(StrainFilter)]
NestedStrainFilterDep = FilterDepends(with_prefix("strain", NestedStrainFilter))


class SpeciesFilterMixin:
    species_id__in: list[uuid.UUID] | None = None
    species: Annotated[NestedSpeciesFilter | None, NestedSpeciesFilterDep] = None
    strain: Annotated[NestedStrainFilter | None, NestedStrainFilterDep] = None
