from typing import Annotated

from app.db.model import Publication
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import EntityFilterMixin, NameFilterMixin


class PublicationFilter(
    CustomFilter,
    NameFilterMixin,
    EntityFilterMixin,
):
    DOI: str | None = None
    publication_year: int | None = None
    publication_year__in: list[int] | None = None
    publication_year__lte: int | None = None
    publication_year__gte: int | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Publication
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "name",
            "publication_year",
        ]


PublicationFilterDep = Annotated[PublicationFilter, FilterDepends(PublicationFilter)]
