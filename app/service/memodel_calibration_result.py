import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload

from app.db.model import MEModelCalibrationResult, Person, Subject
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.memodel_calibration_result import MEModelCalibrationResultFilterDep
from app.queries.common import (
    router_create_one,
    router_delete_one,
    router_read_many,
    router_read_one,
    router_update_one,
)
from app.queries.factory import query_params_factory
from app.schemas.memodel_calibration_result import (
    MEModelCalibrationResultAdminUpdate,
    MEModelCalibrationResultCreate,
    MEModelCalibrationResultRead,
    MEModelCalibrationResultUserUpdate,
)
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(query: sa.Select):
    return query.options(
        joinedload(Subject.species),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> MEModelCalibrationResultRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=MEModelCalibrationResult,
        user_context=user_context,
        response_schema_class=MEModelCalibrationResultRead,
        apply_operations=_load,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> MEModelCalibrationResultRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=MEModelCalibrationResult,
        user_context=None,
        response_schema_class=MEModelCalibrationResultRead,
        apply_operations=_load,
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    json_model: MEModelCalibrationResultCreate,
    db: SessionDep,
) -> MEModelCalibrationResultRead:
    return router_create_one(
        db=db,
        user_context=user_context,
        db_model_class=MEModelCalibrationResult,
        json_model=json_model,
        response_schema_class=MEModelCalibrationResultRead,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: MEModelCalibrationResultUserUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> MEModelCalibrationResultRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=MEModelCalibrationResult,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=MEModelCalibrationResultRead,
        apply_operations=_load,
    )


def admin_update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: MEModelCalibrationResultAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> MEModelCalibrationResultRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=MEModelCalibrationResult,
        user_context=None,
        json_model=json_model,
        response_schema_class=MEModelCalibrationResultRead,
        apply_operations=_load,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: MEModelCalibrationResultFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[MEModelCalibrationResultRead]:
    aliases: Aliases = {
        Person: {
            "created_by": aliased(Person, flat=True),
            "updated_by": aliased(Person, flat=True),
        },
    }
    filter_keys = [
        "created_by",
        "updated_by",
    ]

    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=MEModelCalibrationResult,
        filter_keys=filter_keys,
        facet_keys=[],
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=MEModelCalibrationResult,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=MEModelCalibrationResultRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
    )


def delete_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> DeleteResponse:
    return router_delete_one(
        id_=id_,
        db=db,
        db_model_class=MEModelCalibrationResult,
        user_context=user_context,
    )
