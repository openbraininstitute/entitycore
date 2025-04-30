import uuid
from datetime import datetime, timedelta
from typing import Annotated, TYPE_CHECKING
from pydantic import UUID4, BaseModel, ConfigDict

from datetime import date

#if TYPE_CHECKING:
from app.schemas.agent import PersonRead
from app.schemas.contribution import ContributionReadWithoutEntity
 
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

class ScientificArtifactMixin(BaseModel):
    name :str
    description:str  
    subject_id : Optional[uuid.UUID] = None
    
    brain_region_id: int
    additional_brain_regions: Optional[list[int]] | None
    license_id: Optional[uuid.UUID] = None #only needed when public 
    experiment_date: Optional[date] 

    PublishedIn : PublishedInType
    
    validation_tags: dict[str, bool] #This is a dict{“properties_check”: T/F} (determined by a script not a user input. Should this be here or an annotation?) 

    contact_id : uuid.UUID
