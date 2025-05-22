import uuid
from uuid import UUID
from datetime import date, datetime, timedelta
from typing import Annotated, TYPE_CHECKING, List, Optional
from pydantic import UUID4, BaseModel, ConfigDict

from app.schemas.agent import PersonRead
from app.schemas.contribution import ContributionReadWithoutEntity
 
from app.schemas.contribution import ContributionRead
from app.schemas.asset import AssetRead
from app.schemas.base import LicenseRead,BrainRegionRead, EntityTypeMixin
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


class ScientificArtifactBase(EntityTypeMixin):
    model_config = ConfigDict(from_attributes=True)
    creation_date: datetime| None = None
    update_date: Optional[datetime] = None
    name: str
    description: Optional[str] = None
    subject_id : uuid.UUID | None = None
    license_id: Optional[UUID] = None
    authorized_project_id: UUID
    authorized_public: bool = False
    createdBy_id: Optional[UUID] = None
    updatedBy_id: Optional[UUID] = None
    experiment_date: date | None = None 
    published_in : PublishedInType| None = None
    contact_id : uuid.UUID | None = None
    

class ScientificArtifactCreate(ScientificArtifactBase):
    brain_region_id: uuid.UUID | None = None

class ScientificArtifactRead(ScientificArtifactBase):
    id: UUID
    brain_region: BrainRegionRead




