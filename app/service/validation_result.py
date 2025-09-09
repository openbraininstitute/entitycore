import uuid

import sqlalchemy as sa
from sqlalchemy.orm import joinedload, raiseload, selectinload

from app.db.model import Subject, ValidationResult
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.validation_result import ValidationResultFilterDep
from app.queries.common import (
    router_create_one,
    router_read_many,
    router_read_one,
    router_update_one,
)
from app.schemas.types import ListResponse
from app.schemas.validation import (
    ValidationResultCreate,
    ValidationResultRead,
    ValidationResultUpdate,
)


def _load(query: sa.Select):
    return query.options(
        joinedload(Subject.species),
        joinedload(ValidationResult.created_by),
        joinedload(ValidationResult.updated_by),
        selectinload(ValidationResult.assets),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> ValidationResultRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=ValidationResult,
        authorized_project_id=user_context.project_id,
        response_schema_class=ValidationResultRead,
        apply_operations=_load,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> ValidationResultRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=ValidationResult,
        authorized_project_id=None,
        response_schema_class=ValidationResultRead,
        apply_operations=_load,
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    json_model: ValidationResultCreate,
    db: SessionDep,
) -> ValidationResultRead:
    return router_create_one(
        db=db,
        user_context=user_context,
        db_model_class=ValidationResult,
        json_model=json_model,
        response_schema_class=ValidationResultRead,
        apply_operations=_load,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: ValidationResultUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> ValidationResultRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=ValidationResult,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=ValidationResultRead,
        apply_operations=_load,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: ValidationResultFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[ValidationResultRead]:
    aliases = {}
    name_to_facet_query_params = {}
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=ValidationResult,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=ValidationResultRead,
        authorized_project_id=user_context.project_id,
        filter_joins=None,
    )
