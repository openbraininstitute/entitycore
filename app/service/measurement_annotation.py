import uuid
from http import HTTPStatus
from typing import Annotated

import sqlalchemy as sa
from fastapi import Depends
from sqlalchemy.orm import (
    aliased,
    contains_eager,
    raiseload,
    selectinload,
)

from app.db.auth import constrain_entity_query_to_project, constrain_to_readable_entities
from app.db.model import (
    Entity,
    MeasurementAnnotation,
    MeasurementKind,
    MeasurementLabel,
)
from app.db.utils import MEASURABLE_ENTITIES
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ApiError, ApiErrorCode
from app.filters.measurement_annotation import (
    MeasurementAnnotationFilterDep,
)
from app.queries.common import (
    router_admin_delete_one,
    router_create_one,
    router_read_many,
    router_read_one,
    router_update_one,
)
from app.queries.entity import get_writable_entity
from app.queries.factory import query_params_factory
from app.schemas.measurement_annotation import (
    MeasurementAnnotationAdminUpdate,
    MeasurementAnnotationCreate,
    MeasurementAnnotationRead,
    MeasurementAnnotationUserUpdate,
)
from app.schemas.types import ListResponse


def _update_measurement_label_ids(
    db: SessionDep, measurement_annotation: MeasurementAnnotationCreate
) -> MeasurementAnnotationCreate:
    """Update measurement_label_id for each measurement_kind, based on the provided pref_label.

    Any existing ``measurement_kind.measurement_label_id`` is ignored and overridden if present.
    """
    labels = {kind.pref_label for kind in measurement_annotation.measurement_kinds}
    query = sa.select(MeasurementLabel.pref_label, MeasurementLabel.id).where(
        MeasurementLabel.entity_type == measurement_annotation.entity_type,
    )
    allowed_labels = {row.pref_label: row.id for row in db.execute(query)}
    if invalid_labels := labels.difference(allowed_labels):
        raise ApiError(
            message=(
                f"Invalid measurement labels for entity type {measurement_annotation.entity_type}"
            ),
            error_code=ApiErrorCode.INVALID_REQUEST,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            details={
                "invalid_labels": sorted(invalid_labels),
                "allowed_labels": sorted(allowed_labels),
            },
        )
    for measurement_kind in measurement_annotation.measurement_kinds:
        measurement_kind.measurement_label_id = allowed_labels[measurement_kind.pref_label]
    return measurement_annotation


def _load_from_db(q: sa.Select) -> sa.Select:
    return q.options(
        selectinload(MeasurementAnnotation.measurement_kinds).options(
            selectinload(MeasurementKind.measurement_items),
            selectinload(MeasurementKind.measurement_label),
        ),
        contains_eager(MeasurementAnnotation.entity),
        raiseload("*"),
    )


def _load_from_db_with_entity(q: sa.Select) -> sa.Select:
    return q.options(
        selectinload(MeasurementAnnotation.measurement_kinds).options(
            selectinload(MeasurementKind.measurement_items),
            selectinload(MeasurementKind.measurement_label),
        ),
        selectinload(MeasurementAnnotation.entity),
        raiseload("*"),
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    filter_model: MeasurementAnnotationFilterDep,
    pagination_request: PaginationQuery,
) -> ListResponse[MeasurementAnnotationRead]:
    apply_filter_query_operations = lambda q: constrain_to_readable_entities(
        q.join(Entity, Entity.id == MeasurementAnnotation.entity_id),
        project_id=user_context.project_id,
    )
    facet_keys = []
    filter_keys = [
        "measurement_kind",
        "measurement_kind.pref_label",
        "measurement_kind.measurement_item",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=MeasurementAnnotation,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases={},
    )
    return router_read_many(
        db=db,
        db_model_class=MeasurementAnnotation,
        authorized_project_id=None,  # validated with apply_filter_query_operations
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=None,
        apply_filter_query_operations=apply_filter_query_operations,
        apply_data_query_operations=_load_from_db_with_entity,
        pagination_request=pagination_request,
        response_schema_class=MeasurementAnnotationRead,
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=filter_model,
        filter_joins=filter_joins,
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> MeasurementAnnotationRead:
    def apply_operations(q):
        q = q.join(Entity, Entity.id == MeasurementAnnotation.entity_id)
        q = constrain_to_readable_entities(q, project_id=user_context.project_id)
        return _load_from_db(q=q)

    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=MeasurementAnnotation,
        user_context=None,  # validated with apply_operations
        response_schema_class=MeasurementAnnotationRead,
        apply_operations=apply_operations,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> MeasurementAnnotationRead:
    def apply_operations(q):
        q = q.join(Entity, Entity.id == MeasurementAnnotation.entity_id)
        return _load_from_db(q=q)

    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=MeasurementAnnotation,
        user_context=None,
        response_schema_class=MeasurementAnnotationRead,
        apply_operations=apply_operations,
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    measurement_annotation: Annotated[
        MeasurementAnnotationCreate,
        Depends(_update_measurement_label_ids),
    ],
) -> MeasurementAnnotationRead:
    def apply_operations(q):
        q = q.join(Entity, Entity.id == MeasurementAnnotation.entity_id)
        q = constrain_entity_query_to_project(q, project_id=user_context.project_id)
        return _load_from_db(q=q)

    _entity = get_writable_entity(
        db=db,
        db_model_class=MEASURABLE_ENTITIES[measurement_annotation.entity_type],
        entity_id=measurement_annotation.entity_id,
        project_id=user_context.project_id,
    )
    response = router_create_one(
        db=db,
        db_model_class=MeasurementAnnotation,
        user_context=user_context,
        json_model=measurement_annotation,
        response_schema_class=MeasurementAnnotationRead,
        apply_operations=apply_operations,
    )
    return response


def delete_one(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> MeasurementAnnotationRead:
    def apply_operations(q):
        q = q.join(Entity, Entity.id == MeasurementAnnotation.entity_id)
        q = constrain_entity_query_to_project(q, project_id=user_context.project_id)
        return _load_from_db(q=q)

    one = router_read_one(
        id_=id_,
        db=db,
        db_model_class=MeasurementAnnotation,
        user_context=None,  # validated with apply_operations
        response_schema_class=MeasurementAnnotationRead,
        apply_operations=apply_operations,
    )
    router_admin_delete_one(
        id_=id_,
        db=db,
        db_model_class=MeasurementAnnotation,
    )
    return one


def update_one(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: MeasurementAnnotationUserUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> MeasurementAnnotationRead:
    def apply_operations(q):
        entity_alias = aliased(Entity)
        q = q.join(entity_alias, entity_alias.id == MeasurementAnnotation.entity_id)
        q = q.where(entity_alias.authorized_project_id == user_context.project_id)
        return _load_from_db_with_entity(q=q)

    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=MeasurementAnnotation,
        user_context=None,
        json_model=json_model,
        response_schema_class=MeasurementAnnotationRead,
        apply_operations=apply_operations,
    )


def admin_update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: MeasurementAnnotationAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> MeasurementAnnotationRead:
    def apply_operations(q):
        entity_alias = aliased(Entity)
        q = q.join(entity_alias, entity_alias.id == MeasurementAnnotation.entity_id)
        return _load_from_db_with_entity(q=q)

    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=MeasurementAnnotation,
        user_context=None,
        json_model=json_model,
        response_schema_class=MeasurementAnnotationRead,
        apply_operations=apply_operations,
    )
