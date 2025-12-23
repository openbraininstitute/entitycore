from pydantic import ConfigDict

from app.db.utils import MeasurableEntityType
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.annotation import AnnotationBase
from app.schemas.base import CreationMixin, IdentifiableMixin
from app.schemas.utils import make_update_schema


class MeasurementLabelBase(AnnotationBase):
    model_config = ConfigDict(from_attributes=True)
    entity_type: MeasurableEntityType


class MeasurementLabelCreate(MeasurementLabelBase):
    pass


class MeasurementLabelRead(
    MeasurementLabelBase,
    IdentifiableMixin,
    CreationMixin,
    CreatedByUpdatedByMixin,
):
    pass


MeasurementLabelAdminUpdate = make_update_schema(
    MeasurementLabelCreate,
    "MeasurementLabelAdminUpdate",
    excluded_fields={"entity_type"},
)  # pyright : ignore [reportInvalidTypeForm]
