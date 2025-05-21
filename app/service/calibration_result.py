import uuid

import sqlalchemy as sa
from sqlalchemy.orm import joinedload

from app.db.model import Subject, CalibrationResult
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.calibration_result import CalibrationResultFilterDep
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.schemas.types import ListResponse
from app.schemas.calibration import CalibrationResultCreate, CalibrationResultRead


def _load(query: sa.Select):
    return query.options(
        joinedload(Subject.species),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> CalibrationResultRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=CalibrationResult,
        authorized_project_id=user_context.project_id,
        response_schema_class=CalibrationResultRead,
        apply_operations=_load,
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    json_model: CalibrationResultCreate,
    db: SessionDep,
) -> CalibrationResultRead:
    return router_create_one(
        db=db,
        user_context=user_context,
        db_model_class=CalibrationResult,
        json_model=json_model,
        response_schema_class=CalibrationResultRead,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: CalibrationResultFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[CalibrationResultRead]:
    aliases = {}
    name_to_facet_query_params = {}
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=CalibrationResult,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=CalibrationResultRead,
        authorized_project_id=user_context.project_id,
        filter_joins=None,
    )
