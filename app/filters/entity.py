from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import Entity
from app.db.types import EntityType
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import AuthorizedFilterMixin, CreationFilterMixin, IdFilterMixin
from app.filters.person import CreatorFilterMixin


class BasicEntityFilter(CustomFilter):
    type: EntityType | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Entity
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


BasicEntityFilterDep = Annotated[BasicEntityFilter, FilterDepends(BasicEntityFilter)]


class NestedEntityFilter(CustomFilter, IdFilterMixin):
    type: EntityType | None = None

    class Constants(CustomFilter.Constants):
        model = Entity


NestedEntityFilterDep = FilterDepends(with_prefix("entity", NestedEntityFilter))


# Import after class definitions to avoid circular import
from app.filters.contribution import ContributionFilterMixin  # noqa: E402


class EntityFilterMixin(
    IdFilterMixin,
    AuthorizedFilterMixin,
    CreatorFilterMixin,
    CreationFilterMixin,
    ContributionFilterMixin,
):
    pass
