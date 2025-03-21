from pydantic import BaseModel, ConfigDict

from app.schemas.base import CreationMixin, IdentifiableMixin


class MTypeClassBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pref_label: str
    alt_label: str
    definition: str


class MTypeClassRead(MTypeClassBase, CreationMixin, IdentifiableMixin):
    pass
