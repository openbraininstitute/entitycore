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


# Type 'data' conditionally for Pyright or Pydantic
#
# If running Pyright:
# data: Any, The type passed to data can be anything that we're wanting to validate,
# not necessarily a list[M]
#
#  At runtime
# data: list[M] Pydantic will use the type annotation to validate 'data'
# https://docs.pydantic.dev/latest/integrations/visual_studio_code/#strict-errors
class ListResponse[M: BaseModel](BaseModel):
    if TYPE_CHECKING:
        data: Any
    else:
        data: list[M]
    pagination: PaginationResponse
    facets: Facets | None = None
