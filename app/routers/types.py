from typing import Annotated

from fastapi import Query
from pydantic import BaseModel, ConfigDict, field_validator


class PaginationRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    page: int
    page_size: int


class PaginationResponse(BaseModel):
    page: int
    page_size: int
    total_items: int


class Facet(BaseModel):
    id: int
    label: str
    count: int


type Facets = dict[str, list[Facet]]


class ListResponse[M: BaseModel](BaseModel):
    data: list[M]
    pagination: PaginationResponse
    facets: Facets | None = None
