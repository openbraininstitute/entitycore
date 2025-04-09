import uuid

import sqlalchemy as sa
from sqlalchemy.orm import (
    contains_eager,
    raiseload,
    selectinload,
)

from app.db.auth import constrain_to_accessible_entities
from app.db.model import (
    Entity,
    MeasurementAnnotation,
    MeasurementItem,
    MeasurementKind,
)
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.measurement_annotation import MeasurementAnnotationFilterDep
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.queries.entity import get_writable_entity
from app.schemas.measurement_annotation import (
    MeasurementAnnotationCreate,
    MeasurementAnnotationRead,
)
from app.schemas.types import ListResponse
from app.utils.entity import MEASURABLE_ENTITIES


def _load_from_db(q: sa.Select) -> sa.Select:
    return q.options(
        selectinload(MeasurementAnnotation.measurement_kinds).selectinload(
            MeasurementKind.measurement_items
        ),
        contains_eager(MeasurementAnnotation.entity),
        raiseload("*"),
    )


def _load_from_db_with_constraints(q: sa.Select, project_id: uuid.UUID | None) -> sa.Select:
    q = constrain_to_accessible_entities(q.join(Entity), project_id=project_id)
    return _load_from_db(q=q)


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    filter_model: MeasurementAnnotationFilterDep,
    pagination_request: PaginationQuery,
) -> ListResponse[MeasurementAnnotationRead]:
    return router_read_many(
        db=db,
        db_model_class=MeasurementAnnotation,
        authorized_project_id=None,  # validated with apply_filter_query_operations
        with_search=None,
        facets=None,
        aliases=None,
        apply_filter_query_operations=lambda q: constrain_to_accessible_entities(
            q.join(Entity).join(MeasurementKind).join(MeasurementItem),
            project_id=user_context.project_id,
        ),
        apply_data_query_operations=_load_from_db,
        pagination_request=pagination_request,
        response_schema_class=MeasurementAnnotationRead,
        name_to_facet_query_params=None,
        filter_model=filter_model,
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> MeasurementAnnotationRead:
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=MeasurementAnnotation,
        authorized_project_id=None,  # validated with apply_operations
        response_schema_class=MeasurementAnnotationRead,
        apply_operations=lambda q: _load_from_db_with_constraints(
            q, project_id=user_context.project_id
        ),
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    measurement_annotation: MeasurementAnnotationCreate,
) -> MeasurementAnnotationRead:
    entity = get_writable_entity(
        db=db,
        db_model_class=MEASURABLE_ENTITIES[measurement_annotation.entity_type],
        entity_id=measurement_annotation.entity_id,
        project_id=user_context.project_id,
        for_update=True,
    )
    response = router_create_one(
        db=db,
        db_model_class=MeasurementAnnotation,
        authorized_project_id=None,  # not needed for creation
        json_model=measurement_annotation,
        response_schema_class=MeasurementAnnotationRead,
        apply_operations=lambda q: _load_from_db_with_constraints(
            q, project_id=user_context.project_id
        ),
    )
    # activate the new annotation on the entity
    entity.measurement_annotation_id = response.id
    return response
