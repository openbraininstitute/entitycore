from typing import TypeVar

from pydantic import BaseModel

M = TypeVar("M", bound=BaseModel)


class Pagination(BaseModel):
    page: int
    page_size: int
    total_items: int


type Facets = dict[str, dict[str, int]]


class ListResponse[M: BaseModel](BaseModel):
    data: list[M]
    pagination: Pagination
    facets: Facets | None = None
