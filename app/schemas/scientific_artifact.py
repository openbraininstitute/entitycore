import uuid
from datetime import datetime, timedelta
from typing import Annotated, TYPE_CHECKING
from pydantic import UUID4, BaseModel, ConfigDict

from datetime import date

#if TYPE_CHECKING:
from app.schemas.agent import PersonRead
from app.schemas.contribution import ContributionReadWithoutEntity
 
# where was the artifact published?
class IsDefinedByType(BaseModel):
    """
    Represents ways to define or identify an entity, such as by DOI, PMID, UUID, or other means.
    All fields are optional.
    """
    DOI: str | None = None  # Optional DOI (Digital Object Identifier) as a string
    PMID: int | None = None # Optional PMID (PubMed Identifier) as an integer
    UUID: uuid.UUID | None = None # Using uuid.UUID type for clarity, assuming it refers to a standard UUID
    Other: str | None = None # Optional alternative identifier as a string

class ScientificArtifactMixin(BaseModel):
#    id: UUID4
 
    name :str
    description:str  
    subject_id : uuid.UUID
    
    brain_region_id: int
    contributions: list["ContributionReadWithoutEntity"] | None
    license_id: uuid.UUID 
    experiment_date: date 

    IsDefinedBy : IsDefinedByType
    
    validation_tags: dict[str, bool] #This is a dict{“properties_check”: T/F} (determined by a script not a user input. Should this be here or an annotation?) 

    contact_id : uuid.UUID
    contact_email: str

