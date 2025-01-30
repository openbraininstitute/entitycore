from typing import Generic, TypeVar

from pydantic import BaseModel

M = TypeVar("M", bound=BaseModel)


class Pagination(BaseModel):
    page: int
    limit: int
    total: int


class ListResponse(BaseModel, Generic[M]):
    data: list[M]
    pagination: Pagination
    facets: dict[str, dict[str, int]] | None = None
