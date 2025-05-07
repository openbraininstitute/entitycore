from pydantic import BaseModel, ConfigDict

from app.schemas.base import CreationMixin, IdentifiableMixin


class BrainRegionHierarchyNameBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str


class BrainRegionHierarchyNameRead(BrainRegionHierarchyNameBase, CreationMixin, IdentifiableMixin):
    pass
