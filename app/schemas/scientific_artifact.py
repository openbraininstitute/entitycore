import uuid
from uuid import UUID
from datetime import date, datetime
from typing import  Optional, List, TypedDict
from pydantic import BaseModel, ConfigDict

from app.schemas.base import BrainRegionRead
from enum import Enum
from app.schemas.entity import EntityRead

#the nature of the publication
class PublicationType(str, Enum):
    EntitySource = "EntitySource" #where the model is published
    ComponentSource  = "ComponentSource" #source of any one item used in the model
    Application  = "Application" #any publication which uses the model 

class Author(TypedDict):
    name: str
    lastname: str

# where was the artifact published?
class PublicationBase(EntityRead):
    """
    Represents ways to define or identify an entity, such as by DOI, PMID, UUID, or other means.
    All fields are optional.
    """
    DOI: str | None = None  # Optional DOI (Digital Object Identifier) as a string
    PMID: int | None = None # Optional PMID (PubMed Identifier) as an integer
    UUID: uuid.UUID | None = None # Using uuid.UUID type for clarity, assuming it refers to a standard UUID
    original_source_location : str| None = None 
    other: str | None = None # Optional alternative identifier as a string
    title: str | None = None 
    authors: List[Author]| None = None #list of {"name", "lastname"} entries
    url: str | None = None 
    journal: str | None = None 
    publication_year: int | None = None 
    abstract: str | None = None 

class PublicationCreate(PublicationBase):
    pass

class PublishedInBase(BaseModel):
    publication_id: UUID
    publication_type: PublicationType
    scientific_artifact_id: UUID    

class PublishedInCreate(PublishedInBase):
    pass

class ScientificArtifactBase(EntityRead):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    subject_id : uuid.UUID | None = None
    license_id: Optional[UUID] = None
    experiment_date: date | None = None 
    contact_id : uuid.UUID | None = None
    
class ScientificArtifactCreate(ScientificArtifactBase):
    brain_region_id: uuid.UUID | None = None

class ScientificArtifactRead(ScientificArtifactBase):
    id: UUID
    brain_region: BrainRegionRead
    creation_date: datetime| None = None
    update_date: datetime | None = None

