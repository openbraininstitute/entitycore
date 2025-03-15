from pydantic import BaseModel, ConfigDict

from app.schemas.base import CreationMixin


class Annotation(BaseModel, CreationMixin):
    model_config = ConfigDict(from_attributes=True)

    pref_label: str
    alt_label: str
    definition: str


MtypeClassRead = Annotation
EtypeClassRead = Annotation
