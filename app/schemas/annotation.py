from app.schemas.base import CreationMixin, IdentifiableMixin


class Annotation(CreationMixin, IdentifiableMixin):
    pref_label: str
    alt_label: str
    definition: str


MTypeClassRead = Annotation
ETypeClassRead = Annotation
