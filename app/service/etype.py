import uuid

from app.db.model import ETypeClass
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.common import ETypeClassFilterDep
from app.queries.common import (
    router_admin_delete_one,
    router_create_one,
    router_read_many,
    router_read_one,
    router_update_one,
)
from app.schemas.annotation import ETypeClassAdminUpdate, ETypeClassCreate, ETypeClassRead
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse


def read_many(
    db: SessionDep,
    pagination_request: PaginationQuery,
    etype_class_filter: ETypeClassFilterDep,
) -> ListResponse[ETypeClassRead]:
    return router_read_many(
        db=db,
        db_model_class=ETypeClass,
        authorized_project_id=None,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=None,
        apply_filter_query_operations=None,
        apply_data_query_operations=None,
        pagination_request=pagination_request,
        response_schema_class=ETypeClassRead,
        name_to_facet_query_params=None,
        filter_model=etype_class_filter,
    )


def read_one(id_: uuid.UUID, db: SessionDep) -> ETypeClassRead:
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=ETypeClass,
        user_context=None,
        response_schema_class=ETypeClassRead,
        apply_operations=None,
    )


def admin_read_one(db: SessionDep, id_: uuid.UUID) -> ETypeClassRead:
    return read_one(db=db, id_=id_)


def create_one(
    *,
    db: SessionDep,
    json_model: ETypeClassCreate,
    user_context: AdminContextDep,
) -> ETypeClassRead:
    return router_create_one(
        db=db,
        db_model_class=ETypeClass,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=ETypeClassRead,
    )


def update_one(
    db: SessionDep,
    user_context: AdminContextDep,  # noqa: ARG001
    id_: uuid.UUID,
    json_model: ETypeClassAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> ETypeClassRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=ETypeClass,
        user_context=None,
        json_model=json_model,
        response_schema_class=ETypeClassRead,
    )


def admin_update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: ETypeClassAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> ETypeClassRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=ETypeClass,
        user_context=None,
        json_model=json_model,
        response_schema_class=ETypeClassRead,
    )


def delete_one(
    db: SessionDep,
    id_: uuid.UUID,
    user_context: AdminContextDep,  # noqa: ARG001
) -> DeleteResponse:
    return router_admin_delete_one(
        id_=id_,
        db=db,
        db_model_class=ETypeClass,
    )
