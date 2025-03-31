import uuid
from typing import TYPE_CHECKING

import strawberry

import app.service.morphology
from app.dependencies.auth import user_with_project_id
from app.filters.morphology import MorphologyFilter
from app.graphql.filters.morphology import MorphologyFilterInput
from app.graphql.types.morphology import MorphologyInput, MorphologyType
from app.graphql.types.pagination import ListResponseType, PaginationRequestInput
from app.schemas.morphology import ReconstructionMorphologyCreate, ReconstructionMorphologyRead
from app.schemas.types import PaginationRequest

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.schemas.auth import UserContext, UserContextWithProjectId


@strawberry.type
class MorphologyQuery:
    @strawberry.field
    def read_many_morphologies(
        self,
        *,
        info: strawberry.Info,
        pagination_request: PaginationRequestInput,
        morphology_filter: MorphologyFilterInput,
        search: str | None = None,
        with_facets: bool = False,
    ) -> ListResponseType[MorphologyType, ReconstructionMorphologyRead]:
        # for proper validation, validate the input and return a pydantic model
        db: Session = info.context.db
        user_context: UserContext = info.context.user_context
        validated_pagination_request = PaginationRequest.model_validate(
            pagination_request, from_attributes=True
        )
        validated_morphology_filter = MorphologyFilter.model_validate(
            morphology_filter, from_attributes=True
        )
        result = app.service.morphology.read_many(
            user_context=user_context,
            db=db,
            pagination_request=validated_pagination_request,
            morphology_filter=validated_morphology_filter,
            search=search,
            with_facets=with_facets,
        )
        return ListResponseType[MorphologyType, ReconstructionMorphologyRead].from_pydantic(result)

    @strawberry.field
    def read_morphology(self, id_: uuid.UUID, info: strawberry.Info) -> MorphologyType | None:
        # for proper validation, validate the input and return a pydantic model
        db: Session = info.context.db
        user_context: UserContext = info.context.user_context
        result = app.service.morphology.read_one(user_context=user_context, db=db, id_=id_)
        return MorphologyType.from_pydantic(result) if result else None


@strawberry.type
class MorphologyMutation:
    @strawberry.mutation
    def create_morphology(
        self, morphology: MorphologyInput, info: strawberry.Info
    ) -> MorphologyType:
        # for proper validation, validate the input and return a pydantic model
        db: Session = info.context.db
        user_context: UserContextWithProjectId = user_with_project_id(info.context.user_context)
        validated = ReconstructionMorphologyCreate.model_validate(morphology)
        result = app.service.morphology.create_one(
            user_context=user_context, db=db, reconstruction=validated
        )
        return MorphologyType.from_pydantic(result)
