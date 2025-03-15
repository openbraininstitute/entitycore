from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, computed_field
from sqlalchemy import Select
from sqlalchemy.orm import Query


class PaginationRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page: Annotated[int, Field(ge=1)] = 1
    page_size: Annotated[int, Field(ge=1)] = 100

    @computed_field  # type: ignore[prop-decorator]
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    def paginate_query(self, q: Query | Select):
        return q.limit(self.page_size).offset(self.offset)


class PaginationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page: int
    page_size: int
    total_items: int


class Facet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str
    count: int
    type: str | None


type Facets = dict[str, list[Facet]]


class ListResponse[M: BaseModel](BaseModel):
    data: list[M]
    pagination: PaginationResponse
    facets: Facets | None = None
