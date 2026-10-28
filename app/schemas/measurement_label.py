from app.db.utils import MeasurableEntityType
from app.schemas.annotation import AnnotationBase
from app.schemas.identifiable import IdentifiableCreate, IdentifiableRead
from app.schemas.utils import make_update_schema


class MeasurementLabelBase(AnnotationBase):
    entity_type: MeasurableEntityType


class MeasurementLabelCreate(MeasurementLabelBase, IdentifiableCreate):
    pass


class MeasurementLabelRead(
    MeasurementLabelBase,
    IdentifiableRead,
):
    pass


MeasurementLabelAdminUpdate = make_update_schema(
    MeasurementLabelCreate,
    "MeasurementLabelAdminUpdate",
    excluded_fields={"entity_type"},
)  # pyright : ignore [reportInvalidTypeForm]
