from pydantic import BaseModel, ConfigDict, computed_field


class PaginationRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page: int
    page_size: int

    @computed_field  # type: ignore[prop-decorator]
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

    id: int
    label: str
    count: int
    type: str | None


type Facets = dict[str, list[Facet]]


class ListResponse[M: BaseModel](BaseModel):
    data: list[M]
    pagination: PaginationResponse
    facets: Facets | None = None
