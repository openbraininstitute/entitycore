import uuid
from typing import Annotated

import sqlalchemy as sa
from pydantic import AnyUrl, BaseModel, ConfigDict, Field, HttpUrl, PlainSerializer, computed_field
from sqlalchemy.orm import DeclarativeBase


class PaginationRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page: Annotated[int, Field(ge=1)] = 1
    page_size: Annotated[int, Field(ge=1)] = 100

    @computed_field
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page: int
    page_size: int
    total_items: int


class Facet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | int  # int is for brain region
    label: str
    count: int
    type: str | None


type Facets = dict[str, list[Facet]]


class ListResponse[M: BaseModel](BaseModel):
    data: list[M]
    pagination: PaginationResponse
    facets: Facets | None = None


type Select[M: DeclarativeBase] = sa.Select[tuple[M]]


# The URL's encoded string, using the punycode-encoded host for serialization to the db.
SerializableHttpUrl = Annotated[
    HttpUrl,
    PlainSerializer(lambda x: x.encoded_string(), return_type=str, when_used="unless-none"),
]
SerializableAnyUrl = Annotated[
    AnyUrl,
    PlainSerializer(lambda x: x.encoded_string(), return_type=str, when_used="unless-none"),
]
