from pydantic import BaseModel

from app.schemas.base import CreationMixin, IdentifiableMixin
from app.schemas.utils import make_update_schema


class AnnotationBase(BaseModel):
    pref_label: str
    alt_label: str
    definition: str


class AnnotationRead(AnnotationBase, CreationMixin, IdentifiableMixin):
    pass


class AnnotationCreate(AnnotationBase):
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
