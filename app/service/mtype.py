import uuid

from app.db.model import MTypeClass
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.common import MTypeClassFilterDep
from app.queries.common import (
    router_create_one,
    router_delete_one,
    router_read_many,
    router_read_one,
    router_update_one,
)
from app.schemas.annotation import MTypeClassAdminUpdate, MTypeClassCreate, MTypeClassRead
from app.schemas.types import ListResponse


def read_many(
    db: SessionDep,
    pagination_request: PaginationQuery,
    mtype_class_filter: MTypeClassFilterDep,
) -> ListResponse[MTypeClassRead]:
    return router_read_many(
        db=db,
        db_model_class=MTypeClass,
        authorized_project_id=None,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=None,
        apply_filter_query_operations=None,
        apply_data_query_operations=None,
        pagination_request=pagination_request,
        response_schema_class=MTypeClassRead,
        name_to_facet_query_params=None,
        filter_model=mtype_class_filter,
    )


def read_one(id_: uuid.UUID, db: SessionDep) -> MTypeClassRead:
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=MTypeClass,
        authorized_project_id=None,
        response_schema_class=MTypeClassRead,
        apply_operations=None,
    )


def admin_read_one(db: SessionDep, id_: uuid.UUID) -> MTypeClassRead:
    return read_one(db=db, id_=id_)


def create_one(
    *,
    db: SessionDep,
    json_model: MTypeClassCreate,
    user_context: AdminContextDep,
) -> MTypeClassRead:
    return router_create_one(
        db=db,
        db_model_class=MTypeClass,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=MTypeClassRead,
    )


def update_one(
    db: SessionDep,
    user_context: AdminContextDep,  # noqa: ARG001
    id_: uuid.UUID,
    json_model: MTypeClassAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> MTypeClassRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=MTypeClass,
        user_context=None,
        json_model=json_model,
        response_schema_class=MTypeClassRead,
    )


def admin_update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: MTypeClassAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> MTypeClassRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=MTypeClass,
        user_context=None,
        json_model=json_model,
        response_schema_class=MTypeClassRead,
    )


def delete_one(
    db: SessionDep,
    id_: uuid.UUID,
    user_context: AdminContextDep,  # noqa: ARG001
):
    return router_delete_one(
        id_=id_,
        db=db,
        db_model_class=MTypeClass,
        user_context=None,
    )
