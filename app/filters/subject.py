from datetime import timedelta
from typing import Annotated

from app.db.model import Subject
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter, Prefix
from app.filters.common import (
    IdFilterMixin,
    ILikeSearchFilterMixin,
    NameFilterMixin,
)
from app.filters.entity import EntityFilterMixin
from app.filters.species import NestedSpeciesFilter, NestedStrainFilter, SpeciesFilterMixin


class NestedSubjectFilter(IdFilterMixin, NameFilterMixin, CustomFilter):
    age_value: timedelta | None = None

    species: Annotated[NestedSpeciesFilter | None, Prefix(value="subject__species")] = None

    strain: Annotated[NestedStrainFilter | None, Prefix(value="subject__strain")] = None

    class Constants(CustomFilter.Constants):
        model = Subject


class SubjectFilter(
    EntityFilterMixin,
    SpeciesFilterMixin,
    NameFilterMixin,
    ILikeSearchFilterMixin,
    CustomFilter,
):
    age_value: timedelta | None = None

    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = Subject
        ordering_model_fields = ["creation_date"]  # ruff:ignore[mutable-class-default]


SubjectFilterDep = Annotated[SubjectFilter, FilterDepends(SubjectFilter)]


class SubjectFilterMixin:
    subject: NestedSubjectFilter | None = None
