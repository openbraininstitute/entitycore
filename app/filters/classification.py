import uuid
from typing import Annotated

from app.db.model import ETypeClassification, MTypeClassification
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    CreatorFilterMixin,
)


class MTypeClassificationFilter(CreatorFilterMixin, CustomFilter):
    entity_id: uuid.UUID | None = None
    mtype_class_id: uuid.UUID | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = MTypeClassification
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
        ]


class ETypeClassificationFilter(CreatorFilterMixin, CustomFilter):
    entity_id: uuid.UUID | None = None
    etype_class_id: uuid.UUID | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = ETypeClassification
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
        ]


MTypeClassificationFilterDep = Annotated[
    MTypeClassificationFilter, FilterDepends(MTypeClassificationFilter)
]
ETypeClassificationFilterDep = Annotated[
    ETypeClassificationFilter, FilterDepends(ETypeClassificationFilter)
]
