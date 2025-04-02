import strawberry
from graphql import GraphQLError
from strawberry.schema.config import StrawberryConfig
from strawberry.types import ExecutionContext

from app.graphql.resolvers.morphology import MorphologyMutation, MorphologyQuery
from app.graphql.resolvers.species import SpeciesMutation, SpeciesQuery


@strawberry.type
class Query(
    MorphologyQuery,
    SpeciesQuery,
):
    pass


@strawberry.type
class Mutation(
    MorphologyMutation,
    SpeciesMutation,
):
    pass


class CustomSchema(strawberry.Schema):
    def process_errors(
        self,
        errors: list[GraphQLError],
        execution_context: ExecutionContext | None = None,
    ) -> None:
        for error in errors:
            # temporary workaround to propagate the exception to the FastAPI handlers,
            # although this does not follow the GraphQL specifications
            if err := getattr(error, "original_error", None):
                raise err
        super().process_errors(errors, execution_context)


schema = CustomSchema(
    query=Query,
    mutation=Mutation,
    config=StrawberryConfig(auto_camel_case=False),
)
