from pydantic import BaseModel, ConfigDict

from app.schemas.base import BrainRegionRead, CreationMixin, IdentifiableMixin


class MEModelBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    status: str
    validated: bool = False


class MEModelCreate(MEModelBase):
    brain_region_id: int


class MEModelRead(
    MEModelBase,
    IdentifiableMixin,
    CreationMixin,
):
    brain_region: BrainRegionRead
