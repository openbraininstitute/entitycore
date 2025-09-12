from typing import Annotated

from app.db.model import Role
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter


class RoleFilter(CustomFilter):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Role
        ordering_model_fields = ["creation_date"]  # noqa: RUF012


RoleFilterDep = Annotated[RoleFilter, FilterDepends(RoleFilter)]
