import uuid

from app.db.model import Role
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.role import RoleFilterDep
from app.queries.common import (
    router_create_one,
    router_delete_one,
    router_read_many,
    router_read_one,
    router_update_one,
)
from app.schemas.role import RoleAdminUpdate, RoleCreate, RoleRead
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse


def read_many(
    db: SessionDep, pagination_request: PaginationQuery, filter_model: RoleFilterDep
) -> ListResponse[RoleRead]:
    return router_read_many(
        db=db,
        db_model_class=Role,
        authorized_project_id=None,
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
        authorized_project_id=None,
        response_schema_class=RoleRead,
        apply_operations=None,
    )


def admin_read_one(db: SessionDep, id_: uuid.UUID) -> RoleRead:
    return read_one(db=db, id_=id_)


def create_one(json_model: RoleCreate, db: SessionDep, user_context: AdminContextDep) -> RoleRead:
    return router_create_one(
        db=db,
        db_model_class=Role,
        json_model=json_model,
        response_schema_class=RoleRead,
        user_context=user_context,
    )


def update_one(
    db: SessionDep,
    user_context: AdminContextDep,  # noqa: ARG001
    id_: uuid.UUID,
    json_model: RoleAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> RoleRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=Role,
        user_context=None,
        json_model=json_model,
        response_schema_class=RoleRead,
    )


def admin_update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: RoleAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> RoleRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=Role,
        user_context=None,
        json_model=json_model,
        response_schema_class=RoleRead,
    )


def delete_one(
    db: SessionDep,
    id_: uuid.UUID,
    user_context: AdminContextDep,  # noqa: ARG001
) -> DeleteResponse:
    return router_delete_one(
        id_=id_,
        db=db,
        db_model_class=Role,
        user_context=None,
    )
