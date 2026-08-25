import uuid

import sqlalchemy as sa
from sqlalchemy.orm import joinedload, raiseload

import app.queries.common
from app.db.model import MeasurementLabel
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.measurement_label import MeasurementLabelFilterDep
from app.queries.factory import query_params_factory
from app.schemas.measurement_label import (
    MeasurementLabelAdminUpdate,
    MeasurementLabelCreate,
    MeasurementLabelRead,
)
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse


def _load(query: sa.Select):
    return query.options(
        joinedload(MeasurementLabel.created_by),
        joinedload(MeasurementLabel.updated_by),
        raiseload("*"),
    )


def read_one(
    *,
    db: SessionDep,
    id_: uuid.UUID,
) -> MeasurementLabelRead:
    return app.queries.common.router_read_one(
        id_=id_,
        db=db,
        db_model_class=MeasurementLabel,
        user_context=None,
        response_schema_class=MeasurementLabelRead,
        apply_operations=_load,
    )


def admin_read_one(
    *,
    db: SessionDep,
    id_: uuid.UUID,
) -> MeasurementLabelRead:
    return read_one(id_=id_, db=db)


def create_one(
    *,
    db: SessionDep,
    json_model: MeasurementLabelCreate,
    user_context: AdminContextDep,
) -> MeasurementLabelRead:
    return app.queries.common.router_create_one(
        db=db,
        db_model_class=MeasurementLabel,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=MeasurementLabelRead,
        apply_operations=_load,
    )


def read_many(
    *,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: MeasurementLabelFilterDep,
) -> ListResponse[MeasurementLabelRead]:
    facet_keys = filter_keys = [
        "created_by",
        "updated_by",
    ]
    name_to_facet_query_params, join_specs, aliases = query_params_factory(
        db_model_class=MeasurementLabel,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
    )
    return app.queries.common.router_read_many(
        db=db,
        db_model_class=MeasurementLabel,
        authorized_project_id=None,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=aliases,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        pagination_request=pagination_request,
        response_schema_class=MeasurementLabelRead,
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=filter_model,
        join_specs=join_specs,
    )


admin_read_many = read_many


def update_one(
    db: SessionDep,
    user_context: AdminContextDep,
    id_: uuid.UUID,
    json_model: MeasurementLabelAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> MeasurementLabelRead:
    return app.queries.common.router_update_one(
        id_=id_,
        db=db,
        db_model_class=MeasurementLabel,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=MeasurementLabelRead,
        check_authorized_project=False,
    )


admin_update_one = update_one


def delete_one(
    db: SessionDep,
    id_: uuid.UUID,
    user_context: AdminContextDep,  # ruff:ignore[unused-function-argument]
) -> DeleteResponse:
    return app.queries.common.router_admin_delete_one(
        id_=id_,
        db=db,
        db_model_class=MeasurementLabel,
    )
