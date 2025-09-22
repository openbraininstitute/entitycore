import uuid

import sqlalchemy as sa
from sqlalchemy.orm import joinedload, raiseload

from app.db.model import Subject
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import FacetsDep, PaginationQuery, SearchDep
from app.dependencies.db import SessionDep
from app.filters.subject import SubjectFilterDep
from app.queries.common import (
    router_create_one,
    router_read_many,
    router_read_one,
    router_update_one,
)
from app.queries.factory import query_params_factory
from app.schemas.subject import SubjectAdminUpdate, SubjectCreate, SubjectRead, SubjectUserUpdate
from app.schemas.types import ListResponse


def _load(query: sa.Select):
    return query.options(
        joinedload(Subject.species),
        joinedload(Subject.strain),
        joinedload(Subject.created_by),
        joinedload(Subject.updated_by),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> SubjectRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=Subject,
        authorized_project_id=user_context.project_id,
        response_schema_class=SubjectRead,
        apply_operations=_load,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> SubjectRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=Subject,
        authorized_project_id=None,
        response_schema_class=SubjectRead,
        apply_operations=_load,
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    json_model: SubjectCreate,
) -> SubjectRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        db_model_class=Subject,
        user_context=user_context,
        response_schema_class=SubjectRead,
        apply_operations=_load,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: SubjectUserUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> SubjectRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=Subject,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=SubjectRead,
        apply_operations=_load,
    )


def admin_update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: SubjectAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> SubjectRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=Subject,
        user_context=None,
        json_model=json_model,
        response_schema_class=SubjectRead,
        apply_operations=_load,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: SubjectFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
) -> ListResponse[SubjectRead]:
    facet_keys = filter_keys = [
        "contribution",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=Subject,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases={},
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=Subject,
        with_search=with_search,
        with_in_brain_region=None,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases={},
        pagination_request=pagination_request,
        response_schema_class=SubjectRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
    )
