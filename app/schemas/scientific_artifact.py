import uuid
from uuid import UUID
from datetime import date, datetime, timedelta
from typing import Annotated, TYPE_CHECKING, List, Optional
from pydantic import UUID4, BaseModel, ConfigDict

from app.schemas.agent import PersonRead
from app.schemas.contribution import ContributionReadWithoutEntity
 
#from app.schemas.base import BaseSchema
from app.schemas.contribution import ContributionRead
from app.schemas.asset import AssetRead
from app.schemas.base import LicenseRead
from app.db.model import Entity

# where was the artifact published?
class PublishedInType(BaseModel):
    """
    Represents ways to define or identify an entity, such as by DOI, PMID, UUID, or other means.
    All fields are optional.
    """
    DOI: str | None = None  # Optional DOI (Digital Object Identifier) as a string
    PMID: int | None = None # Optional PMID (PubMed Identifier) as an integer
    UUID: uuid.UUID | None = None # Using uuid.UUID type for clarity, assuming it refers to a standard UUID
    original_source_location : str
    other: str | None = None # Optional alternative identifier as a string

from app.filters.common import BrainRegionFilterMixin

#class ScientificArtifactMixin(BaseModel,BrainRegionFilterMixin):
#    name :str
#    description:str  
#    subject_id : uuid.UUID | None = None
#    license_id: uuid.UUID | None = None #only needed when public 
#    experiment_date: date | None = None 
#    PublishedIn : PublishedInType
#    validation_tags: dict[str, bool] #This is a dict{“properties_check”: T/F} (determined by a script not a user input. Should this be here or an annotation?) 
#    contact_id : uuid.UUID | None = None

#    class Config:
#        from_attributes = True  # Allow mapping from SQLAlchemy objects


class ScientificArtifactCreate(BaseModel,BrainRegionFilterMixin):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: Optional[str] = None
    subject_id : uuid.UUID | None = None
    license_id: Optional[UUID] = None
    authorized_project_id: UUID
    authorized_public: bool = False
    createdBy_id: Optional[UUID] = None
    updatedBy_id: Optional[UUID] = None
    experiment_date: date | None = None 
    published_in : PublishedInType
    validation_tags: dict[str, bool] #This is a dict{“properties_check”: T/F} (determined by a script not a user input. Should this be here or an annotation?) 
    contact_id : uuid.UUID | None = None


class ScientificArtifactRead(ScientificArtifactCreate,BrainRegionFilterMixin):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    creation_date: str
    update_date: Optional[str] = None


#class ScientificArtifactCreate(ScientificArtifactBase):
#    pass

#class ScientificArtifactRead(ScientificArtifactBase):
#    id: UUID
#    creation_date: datetime
#    update_date: datetime
#    authorized_project_id: Optional[UUID] = None
#    license: Optional[LicenseRead] = None
#    contributions: List[ContributionRead] = []
#    assets: List[AssetRead] = []

#    class Config:
#        from_attributes = True




