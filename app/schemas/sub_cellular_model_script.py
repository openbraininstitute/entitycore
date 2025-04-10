import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.asset import AssetRead
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    BrainRegionRead,
    CreationMixin,
    IdentifiableMixin,
    LicensedCreateMixin,
    LicensedReadMixin,
    SubjectRead,
)


class SubCellularModelScriptBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    temperature: Annotated[
        float | None,
        Field(
            title="temperature",
            description=(
                "The temperature at which the mechanism has been built to work on, in Celsius."
            ),
        ),
    ] = None
    is_temperature_dependent: Annotated[
        bool,
        Field(
            title="is temperature dependent",
            description="Whether the mechanism changes depending on temperature or not",
        ),
    ] = False
    is_ljp_corrected: Annotated[
        bool,
        Field(
            title="is ljp corrected",
            description="Whether the mechanism is corrected for liquid junction potential or not",
        ),
    ] = False
    stochastic: Annotated[
        bool,
        Field(
            title="stochastic",
            description="Can the mechanisms behave stochastically",
        ),
    ] = False


class SubCellularModelScriptCreate(
    SubCellularModelScriptBase, LicensedCreateMixin, AuthorizationOptionalPublicMixin
):
    subject_id: uuid.UUID
    brain_region_id: uuid.UUID


class SubCellularModelScriptRead(
    SubCellularModelScriptBase,
    CreationMixin,
    LicensedReadMixin,
    AuthorizationMixin,
    IdentifiableMixin,
):
    subject: SubjectRead
    brain_region: BrainRegionRead
    assets: list[AssetRead] | None
