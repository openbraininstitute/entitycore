import uuid

from app.schemas.base import CreationMixin


class Annotation(CreationMixin):
    id: uuid.UUID
    pref_label: str
    alt_label: str
    definition: str


MTypeClassRead = Annotation
ETypeClassRead = Annotation
