import uuid

import strawberry
from pydantic import BaseModel

from app.schemas.types import Facet, ListResponse, PaginationRequest, PaginationResponse


@strawberry.experimental.pydantic.input(model=PaginationRequest, all_fields=True)
class PaginationRequestInput:
    pass


@strawberry.experimental.pydantic.type(model=PaginationResponse, all_fields=True)
class PaginationResponseType:
    pass


@strawberry.experimental.pydantic.type(model=Facet)
class FacetType:
    id: uuid.UUID  # not working with BrainRegion because using int id
    label: strawberry.auto
    count: strawberry.auto
    type: strawberry.auto


@strawberry.type
class KeyValue[T]:
    key: str
    value: list[T]


@strawberry.type
class ListResponseType[T, M: BaseModel]:
    """ListResponseType, with facets redefined to be compatible with GraphQL."""

    data: list[T]
    pagination: PaginationResponseType
    facets: list[KeyValue[FacetType]] | None = None  # Replaces dict[str, list[Facet]]

    @classmethod
    def from_pydantic(cls, instance: ListResponse[M]) -> "ListResponseType[T, M]":
        if instance.facets:
            facets = [
                KeyValue[FacetType](
                    key=facet_type,
                    value=[FacetType.from_pydantic(facet) for facet in facet_list],
                )
                for facet_type, facet_list in instance.facets.items()
            ]
        else:
            facets = None
        return cls(
            data=instance.data,  # type: ignore[arg-type]
            pagination=PaginationResponseType.from_pydantic(instance.pagination),
            facets=facets,
        )

    def to_pydantic(self) -> ListResponse[M]:
        facets = {kv.key: kv.value for kv in self.facets} if self.facets else None
        return ListResponse[M](
            data=self.data,
            pagination=self.pagination,
            facets=facets,
        )
