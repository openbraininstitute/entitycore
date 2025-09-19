import uuid

from app.db.model import Role
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.role import RoleFilterDep
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.schemas.role import RoleCreate, RoleRead
from app.schemas.types import ListResponse


def read_many(
    db: SessionDep, pagination_request: PaginationQuery, filter_model: RoleFilterDep
) -> ListResponse[RoleRead]:
    return router_read_many(
        db=db,
        db_model_class=Role,
        user_context=None,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=None,
        apply_filter_query_operations=None,
        apply_data_query_operations=None,
        pagination_request=pagination_request,
        response_schema_class=RoleRead,
        name_to_facet_query_params=None,
        filter_model=filter_model,
    )


def read_one(id_: uuid.UUID, db: SessionDep) -> RoleRead:
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=Role,
        user_context=None,
        response_schema_class=RoleRead,
        apply_operations=None,
    )


def create_one(json_model: RoleCreate, db: SessionDep, user_context: AdminContextDep) -> RoleRead:
    return router_create_one(
        db=db,
        db_model_class=Role,
        json_model=json_model,
        response_schema_class=RoleRead,
        user_context=user_context,
    )
