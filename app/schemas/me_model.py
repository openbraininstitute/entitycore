from pydantic import ConfigDict

from app.schemas.base import BrainRegionRead, CreationMixin


class MEModelCreate(CreationMixin):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str
    status: str
    validated: bool = False
    brain_region_id: int
    mmodel_id: int
    emodel_id: int


class MEModelRead(MEModelCreate):
    brain_region: BrainRegionRead
