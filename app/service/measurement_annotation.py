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
from app.filters.measurement_annotation import (
    MeasurementAnnotationFilter,
    MeasurementAnnotationFilterDep,
)
from app.queries.common import ApplyOperations, router_create_one, router_read_many, router_read_one
from app.queries.entity import get_writable_entity
from app.schemas.measurement_annotation import (
    MeasurementAnnotationCreate,
    MeasurementAnnotationRead,
)
from app.schemas.types import ListResponse
from app.utils.entity import MEASURABLE_ENTITIES, MeasurableEntityType


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


def _get_join_params(filter_model: MeasurementAnnotationFilter):
    # this allows to filter by `is_active`, and it's needed because `measurement_annotation_id`
    # is defined in the abstract class MeasurableEntity, and not in the entity table
    match (filter_model.entity_type, filter_model.is_active):
        case (None, None):
            entity_class = Entity
            join_args = []
        case (MeasurableEntityType(), True):
            entity_class = MEASURABLE_ENTITIES[filter_model.entity_type]
            join_args = [entity_class.measurement_annotation_id == MeasurementAnnotation.id]
        case (MeasurableEntityType(), False):
            entity_class = MEASURABLE_ENTITIES[filter_model.entity_type]
            join_args = [
                sa.and_(
                    entity_class.measurement_annotation_id != MeasurementAnnotation.id,
                    entity_class.id == MeasurementAnnotation.entity_id,
                )
            ]
        case (MeasurableEntityType(), None):
            entity_class = Entity
            join_args = [
                sa.and_(
                    entity_class.id == MeasurementAnnotation.entity_id,
                    entity_class.type == filter_model.entity_type,
                )
            ]
        case _:
            msg = "Unexpected error"
            raise RuntimeError(msg)
    # clean the filters so they are ignored by the custom filter
    filter_model.is_active = None
    filter_model.entity_type = None
    return entity_class, join_args


def _get_filter_function(
    filter_model: MeasurementAnnotationFilter, project_id: uuid.UUID | None
) -> ApplyOperations:
    """Return the base query needed to filter the annotations."""

    def _filter_from_db(q: sa.Select) -> sa.Select:
        entity_class, join_args = _get_join_params(filter_model)
        q = q.join(entity_class, *join_args)
        q = constrain_to_accessible_entities(q, project_id=project_id)
        # join only if needed, for better performances
        if filter_model.measurement_kind and filter_model.measurement_kind.has_filtering_fields():
            q = q.join(MeasurementKind)
            if (
                filter_model.measurement_kind.measurement_item
                and filter_model.measurement_kind.measurement_item.has_filtering_fields()
            ):
                q = q.join(MeasurementItem)
        return q

    return _filter_from_db


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
        apply_filter_query_operations=_get_filter_function(
            filter_model=filter_model, project_id=user_context.project_id
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
    response.is_active = True
    return response
