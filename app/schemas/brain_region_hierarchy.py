from pydantic import BaseModel, ConfigDict

from app.schemas.base import CreationMixin, IdentifiableMixin


class BrainRegionHierarchyBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str


class BrainRegionHierarchyRead(BrainRegionHierarchyBase, CreationMixin, IdentifiableMixin):
    pass
