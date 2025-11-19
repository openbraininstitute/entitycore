from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    BrainRegionCreateMixin,
    BrainRegionReadMixin,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
    LicenseCreateMixin,
    LicenseReadMixin,
)
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.subject import SubjectCreateMixin, SubjectReadMixin


class ScientificArtifactBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    ScientificArtifactBase,
    IdentifiableMixin,
    EntityTypeMixin,
    AuthorizationMixin,
):
    pass


class ScientificArtifactRead(
    NestedScientificArtifactRead,
    SubjectReadMixin,
    BrainRegionReadMixin,
    CreatedByUpdatedByMixin,
    CreationMixin,
    LicenseReadMixin,
    AssetsMixin,
    ContributionReadWithoutEntityMixin,
):
    pass


class ScientificArtifactCreate(
    ScientificArtifactBase,
    SubjectCreateMixin,
    BrainRegionCreateMixin,
    LicenseCreateMixin,
    AuthorizationOptionalPublicMixin,
):
    pass
