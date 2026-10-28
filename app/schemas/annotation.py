from app.schemas.base import Schema
from app.schemas.identifiable import IdentifiableCreate, NestedIdentifiableRead
from app.schemas.utils import make_update_schema


class AnnotationBase(Schema):
    pref_label: str
    alt_label: str | None = None
    definition: str


class AnnotationRead(AnnotationBase, NestedIdentifiableRead):
    pass


class AnnotationCreate(AnnotationBase, IdentifiableCreate):
    pass


AnnotationAdminUpdate = make_update_schema(
    AnnotationCreate,
    "AnnotationAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


MTypeClassRead = AnnotationRead
ETypeClassRead = AnnotationRead

MTypeClassCreate = AnnotationCreate
ETypeClassCreate = AnnotationCreate

MTypeClassAdminUpdate = AnnotationAdminUpdate
ETypeClassAdminUpdate = AnnotationAdminUpdate
