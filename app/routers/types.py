from pydantic import BaseModel


class Pagination(BaseModel):
    page: int
    page_size: int
    total_items: int


class Facet(BaseModel):
    id: int
    label: str
    count: int
    type: str


type Facets = list[Facet]


class ListResponse[M: BaseModel](BaseModel):
    data: list[M]
    pagination: Pagination
    facets: Facets | None = None
