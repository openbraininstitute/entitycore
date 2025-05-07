from pydantic import BaseModel

from app.db.types import LabelScheme
from app.schemas.base import CreationMixin, IdentifiableMixin


class LabelBase(BaseModel):
    scheme: LabelScheme
    pref_label: str
    definition: str
    alt_label: str | None = None


class LabelCreate(
    LabelBase,
):
    pass


class LabelRead(
    LabelBase,
    CreationMixin,
    IdentifiableMixin,
):
    pass
