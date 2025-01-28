from pydantic import Field

from app.schemas.base import BrainRegionCreate, LicensedCreateMixin
from app.schemas.contribution import ContributionBase


class SingleCellData(LicensedCreateMixin):
    name: str
    description: str
    contributon: list[ContributionBase]
    brain_region: BrainRegionCreate
    subject_id: int = Field(
        ...,
        title="Subject ID",
        description="ID of the subject",
    )
