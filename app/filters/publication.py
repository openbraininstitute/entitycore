from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import Publication
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import CreationFilterMixin, CreatorFilterMixin, IdFilterMixin


class NestedPublicationFilter(
    IdFilterMixin,
    CustomFilter,
):
    DOI: str | None = None
    publication_year: int | None = None
    publication_year__in: list[int] | None = None
    publication_year__lte: int | None = None
    publication_year__gte: int | None = None
    title: str | None = None

    class Constants(CustomFilter.Constants):
        model = Publication


class PublicationFilter(
    CreatorFilterMixin,
    CreationFilterMixin,
    NestedPublicationFilter,
):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(NestedPublicationFilter.Constants):
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "DOI",
            "publication_year",
            "title",
        ]


PublicationFilterDep = Annotated[PublicationFilter, FilterDepends(PublicationFilter)]
NestedPublicationFilterDep = FilterDepends(with_prefix("publication", NestedPublicationFilter))
