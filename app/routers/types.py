from pydantic import BaseModel


class Pagination(BaseModel):
    page: int
    page_size: int
    total_items: int


# Mapping from attribute -> {distinct_value: count}
# ex: "mType": {"L5_TPC": 10, "L6_BAC": 1},
type Facets = dict[str, dict[str, int]]


class ListResponse[M: BaseModel](BaseModel):
    data: list[M]
    pagination: Pagination
    facets: Facets | None = None
