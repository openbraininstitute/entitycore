import uuid
from datetime import datetime, timedelta
from typing import Annotated, TYPE_CHECKING
from pydantic import UUID4, BaseModel, ConfigDict

from datetime import date

#if TYPE_CHECKING:
from app.schemas.agent import PersonRead
from app.schemas.contribution import ContributionReadWithoutEntity

class ScientificArtifactMixin(BaseModel):
 #   id: UUID4
 
    name :str
    description:str  
    subject_id : uuid.UUID
    
    brain_region_id: int
    additional_brain_region_ids: list[int]
    contributions: list["ContributionReadWithoutEntity"] | None
    license_id: uuid.UUID 
    experiment_date: date 

    validations: dict[str, bool] #This is a dict{“properties_check”: T/F} (determined by a script not a user input. Should this be here or an annotation?) 

    contact : PersonRead
    contact_email: str
