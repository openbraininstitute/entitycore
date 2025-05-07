import uuid

import sqlalchemy as sa
from sqlalchemy.orm import (
    contains_eager,
    raiseload,
    selectinload,
)

from app.db.auth import constrain_entity_query_to_project, constrain_to_accessible_entities
from app.db.model import (
    Entity,
    MeasurementAnnotation,
    MeasurementItem,
    MeasurementKind,
)
from app.db.types import LabelScheme
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.measurement_annotation import (
    MeasurementAnnotationFilter,
    MeasurementAnnotationFilterDep,
)
from app.queries.common import (
    ApplyOperations,
    router_create_one,
    router_delete_one,
    router_read_many,
    router_read_one,
)
from app.queries.entity import get_writable_entity
from app.schemas.measurement_annotation import (
    MeasurementAnnotationCreate,
    MeasurementAnnotationRead,
)
from app.schemas.types import ListResponse
from app.service.label import get_labels_to_ids
from app.utils.entity import MEASURABLE_ENTITIES


def _load_from_db(q: sa.Select) -> sa.Select:
    return q.options(
        selectinload(MeasurementAnnotation.measurement_kinds).selectinload(
            MeasurementKind.measurement_items
        ),
        selectinload(MeasurementAnnotation.measurement_kinds).selectinload(MeasurementKind.label),
        contains_eager(MeasurementAnnotation.entity),
        raiseload("*"),
    )


def _get_filter_function(
    filter_model: MeasurementAnnotationFilter, project_id: uuid.UUID | None
) -> ApplyOperations:
    """Return the base query needed to filter the annotations."""

    def _filter_from_db(q: sa.Select) -> sa.Select:
        q = q.join(Entity, Entity.id == MeasurementAnnotation.entity_id)
        q = constrain_to_accessible_entities(q, project_id=project_id)
        # join with kinds and items only if needed, for better performances
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
    def apply_operations(q):
        q = q.join(Entity, Entity.id == MeasurementAnnotation.entity_id)
        q = constrain_to_accessible_entities(q, project_id=user_context.project_id)
        return _load_from_db(q=q)

    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=MeasurementAnnotation,
        authorized_project_id=None,  # validated with apply_operations
        response_schema_class=MeasurementAnnotationRead,
        apply_operations=apply_operations,
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    measurement_annotation: MeasurementAnnotationCreate,
) -> MeasurementAnnotationRead:
    def apply_operations(q):
        q = q.join(Entity, Entity.id == MeasurementAnnotation.entity_id)
        q = constrain_entity_query_to_project(q, project_id=user_context.project_id)
        return _load_from_db(q=q)

    # retrieve label_id from pref_label if needed
    scheme = LabelScheme[f"{MeasurementKind.__tablename__}__{measurement_annotation.entity_type}"]
    labels = {
        kind.pref_label
        for kind in measurement_annotation.measurement_kinds
        if kind.pref_label is not None
    }
    labels_to_ids = get_labels_to_ids(db, scheme=scheme, labels=labels)
    for kind in measurement_annotation.measurement_kinds:
        kind.label_id = labels_to_ids[kind.pref_label]

    _entity = get_writable_entity(
        db=db,
        db_model_class=MEASURABLE_ENTITIES[measurement_annotation.entity_type],
        entity_id=measurement_annotation.entity_id,
        project_id=user_context.project_id,
    )
    response = router_create_one(
        db=db,
        db_model_class=MeasurementAnnotation,
        authorized_project_id=None,  # not needed for creation
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
        authorized_project_id=None,  # validated with apply_operations
        response_schema_class=MeasurementAnnotationRead,
        apply_operations=apply_operations,
    )
    router_delete_one(
        id_=id_,
        db=db,
        db_model_class=MeasurementAnnotation,
        authorized_project_id=None,  # already validated
    )
    return one
