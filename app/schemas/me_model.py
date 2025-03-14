from pydantic import BaseModel, ConfigDict

from app.schemas.base import BrainRegionRead


class MEModelCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str
    status: str
    validated: bool = False
    brain_region_id: int


class MEModelRead(MEModelCreate):
    brain_region: BrainRegionRead
