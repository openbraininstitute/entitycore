from app.db.model import Role
from app.filters.base import CustomFilter
from app.filters.common import NameFilterMixin


class RoleFilter(NameFilterMixin, CustomFilter):
    role_id: str | None = None

    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = Role
        ordering_model_fields = ["creation_date"]  # ruff:ignore[mutable-class-default]
