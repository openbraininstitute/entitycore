import uuid
from datetime import timedelta
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.db.types import AgePeriod, Sex
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    CreationMixin,
    IdentifiableMixin,
)
from app.schemas.species import NestedSpeciesRead


class SubjectBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, ser_json_timedelta="float")

    name: str
    description: str
    sex: Annotated[
        Sex,
        Field(title="Sex", description="Sex of the subject"),
    ]
    weight: Annotated[
        float | None,
        Field(title="Weight", description="Weight in grams", gt=0.0),
    ] = None
    age_value: Annotated[
        timedelta | None,
        Field(title="Age value", description="Age value interval.", gt=timedelta(0)),
    ] = None
    age_min: Annotated[
        timedelta | None,
        Field(title="Minimum age range", description="Minimum age range", gt=timedelta(0)),
    ] = None
    age_max: Annotated[
        timedelta | None,
        Field(title="Maximum age range", description="Maximum age range", gt=timedelta(0)),
    ] = None
    age_period: AgePeriod | None = None

    @model_validator(mode="after")
    def age_period_mandatory_with_age_fields(self):
        """Age period must be provided when age fields are provided."""
        if any([self.age_value, self.age_min, self.age_max]) and not self.age_period:
            msg = "age_period must be provided when age fields are provided"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def either_age_value_or_age_range(self):
        """Either age_value or age_min and age_max must be provided."""
        if self.age_value and any([self.age_min, self.age_max]):
            msg = "age_value and age_min/age_max cannot both be provided"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def min_max_age_range_consistency(self):
        """Age min and max must be provided together or not at all."""
        if self.age_min and self.age_max:
            if self.age_min >= self.age_max:
                msg = "age_max must be greater than age_min"
                raise ValueError(msg)
            return self

        if self.age_min or self.age_max:
            msg = "age_min and age_max must be provided together"
            raise ValueError(msg)

        return self


class SubjectCreate(AuthorizationOptionalPublicMixin, SubjectBase):
    species_id: uuid.UUID


class SubjectRead(SubjectBase, CreationMixin, AuthorizationMixin, IdentifiableMixin):
    species: NestedSpeciesRead
