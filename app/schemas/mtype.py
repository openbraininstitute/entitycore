from pydantic import BaseModel, ConfigDict

from app.schemas.base import CreationMixin


class MTypeBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pref_label: str
    alt_label: str
    definition: str


class MTypeRead(MTypeBase, CreationMixin):
    id: int
