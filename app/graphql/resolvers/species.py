import uuid
from typing import TYPE_CHECKING

import strawberry

import app.service.species
from app.filters.common import SpeciesFilter
from app.graphql.filters.species import SpeciesFilterInput
from app.graphql.types.common import SpeciesInput, SpeciesType
from app.graphql.types.pagination import ListResponseType, PaginationRequestInput
from app.schemas.base import SpeciesCreate, SpeciesRead
from app.schemas.types import PaginationRequest

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@strawberry.type
class SpeciesQuery:
    @strawberry.field
    def read_many_species(
        self,
        *,
        pagination_request: PaginationRequestInput,
        species_filter: SpeciesFilterInput,
        info: strawberry.Info,
    ) -> ListResponseType[SpeciesType, SpeciesRead]:
        # for proper validation, validate the input and return a pydantic model
        db: Session = info.context.db
        validated_pagination_request = PaginationRequest.model_validate(
            pagination_request, from_attributes=True
        )
        validated_species_filter = SpeciesFilter.model_validate(
            species_filter, from_attributes=True
        )
        result = app.service.species.read_many(
            db=db,
            pagination_request=validated_pagination_request,
            species_filter=validated_species_filter,
        )
        return ListResponseType[SpeciesType, SpeciesRead].from_pydantic(result)

    @strawberry.field
    def read_species(self, *, id_: uuid.UUID, info: strawberry.Info) -> SpeciesType | None:
        # for proper validation, validate the input and return a pydantic model
        db: Session = info.context.db
        result = app.service.species.read_one(db=db, id_=id_)
        return SpeciesType.from_pydantic(result) if result else None


@strawberry.type
class SpeciesMutation:
    @strawberry.mutation
    def create_species(self, *, species: SpeciesInput, info: strawberry.Info) -> SpeciesType:
        # for proper validation, validate the input and return a pydantic model
        db: Session = info.context.db
        validated = SpeciesCreate.model_validate(species)
        result = app.service.species.create_one(db=db, species=validated)
        return SpeciesType.from_pydantic(result)
