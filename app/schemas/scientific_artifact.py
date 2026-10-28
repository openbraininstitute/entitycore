from datetime import datetime
from typing import Annotated

from pydantic import Field

from app.schemas.base import (
    Schema,
)
from app.schemas.brain_region import BrainRegionCreateMixin, BrainRegionReadMixin
from app.schemas.entity import EntityCreate, EntityRead, NestedEntityRead
from app.schemas.license import LicenseCreateMixin, LicenseReadMixin
from app.schemas.subject import SubjectCreateMixin, SubjectReadMixin


class ScientificArtifactBase(Schema):
    experiment_date: Annotated[
        datetime | None,
        Field(description="Date of the experiment associated with the artifact."),
    ] = None
    contact_email: Annotated[
        str | None,
        Field(description="Optional string of a contact person's e-mail address."),
    ] = None
    published_in: Annotated[
        str | None,
        Field(description="Optional string with short version of the source publication(s)."),
    ] = None
    notice_text: Annotated[
        str | None,
        Field(
            description=(
                "Text provided by the data creators to inform users about data caveats, "
                "limitations, or required attribution practices."
            )
        ),
    ] = None


class NestedScientificArtifactRead(
    NestedEntityRead,
    ScientificArtifactBase,
):
    pass


class ScientificArtifactRead(
    EntityRead,
    ScientificArtifactBase,
    SubjectReadMixin,
    BrainRegionReadMixin,
    LicenseReadMixin,
):
    pass


class ScientificArtifactCreate(
    EntityCreate,
    ScientificArtifactBase,
    SubjectCreateMixin,
    BrainRegionCreateMixin,
    LicenseCreateMixin,
):
    pass
