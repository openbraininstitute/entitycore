import uuid
from typing import Annotated

from app.db.model import Person
from app.dependencies.filter import FilterDepends
from app.filters.common import AgentFilter, CreatorFilterMixin


class PersonFilter(AgentFilter, CreatorFilterMixin):
    given_name: str | None = None
    given_name__ilike: str | None = None
    family_name: str | None = None
    family_name__ilike: str | None = None
    sub_id: uuid.UUID | None = None
    sub_id__in: list[uuid.UUID] | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(AgentFilter.Constants):
        model = Person
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "pref_label",
            "given_name",
            "family_name",
        ]


PersonFilterDep = Annotated[PersonFilter, FilterDepends(PersonFilter)]
