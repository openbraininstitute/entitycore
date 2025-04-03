import uuid
from typing import TYPE_CHECKING, Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, computed_field


class PaginationRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page: Annotated[int, Field(ge=1)] = 1
    page_size: Annotated[int, Field(ge=1)] = 100

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

    id: uuid.UUID | int  # int is for brain region
    label: str
    count: int
    type: str | None


type Facets = dict[str, list[Facet]]


class ListResponse[M: BaseModel](BaseModel):
    # When using a static type checker (e.g., Pyright, MyPy), 'data' is set to Any.
    # This prevents issues with generic types in Pydantic, since that data might by
    # of any type that we're wanting to validate, not necessarily list[M].
    #
    # At runtime, 'data' is explicitly defined as list[M] so that Pydantic
    # can enforce validation, ensuring that 'data' is always a list of M instances.
    if TYPE_CHECKING:
        data: Any  # Allows flexibility for static type checkers
    else:
        data: list[M]  # Ensures Pydantic validation at runtime
    pagination: PaginationResponse
    facets: Facets | None = None
