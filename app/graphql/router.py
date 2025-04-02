from fastapi import Depends
from sqlalchemy.orm import Session
from strawberry.fastapi import BaseContext, GraphQLRouter

from app.dependencies.auth import UserContextDep, user_with_service_admin_role
from app.dependencies.db import SessionDep
from app.graphql.schema import schema
from app.schemas.auth import UserContext


class Context(BaseContext):
    def __init__(self, *, db: Session, user_context: UserContext) -> None:
        """Initialize a new Context."""
        super().__init__()
        self.db = db
        self.user_context = user_context


def get_context(db: SessionDep, user_context: UserContextDep) -> Context:
    return Context(db=db, user_context=user_context)


graphql_router = GraphQLRouter(
    schema,
    prefix="/graphql",
    graphql_ide="apollo-sandbox",
    context_getter=get_context,
    dependencies=[Depends(user_with_service_admin_role)],
    include_in_schema=False,
)
