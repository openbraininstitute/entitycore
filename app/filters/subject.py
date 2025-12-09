from datetime import timedelta
from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import Subject
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    IdFilterMixin,
    ILikeSearchFilterMixin,
    NameFilterMixin,
)
from app.filters.entity import EntityFilterMixin
from app.filters.species import NestedSpeciesFilter, NestedStrainFilter, SpeciesFilterMixin


class NestedSubjectFilter(IdFilterMixin, NameFilterMixin, CustomFilter):
    age_value: timedelta | None = None

    species: Annotated[
        NestedSpeciesFilter | None,
        FilterDepends(with_prefix("subject__species", NestedSpeciesFilter)),
    ] = None

    strain: Annotated[
        NestedStrainFilter | None,
        FilterDepends(with_prefix("subject__strain", NestedStrainFilter)),
    ] = None

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

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Subject
        ordering_model_fields = ["creation_date"]  # noqa: RUF012


SubjectFilterDep = Annotated[SubjectFilter, FilterDepends(SubjectFilter)]
NestedSubjectFilterDep = FilterDepends(with_prefix("subject", NestedSubjectFilter))


class SubjectFilterMixin:
    subject: Annotated[NestedSubjectFilter | None, NestedSubjectFilterDep] = None
