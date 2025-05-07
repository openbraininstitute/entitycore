import uuid
from http import HTTPStatus

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.db.model import Label
from app.db.types import LabelScheme
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ApiError, ApiErrorCode
from app.filters.label import LabelFilterDep
from app.queries.common import (
    router_create_one,
    router_delete_one,
    router_read_many,
    router_read_one,
)
from app.schemas.label import LabelCreate, LabelRead
from app.schemas.types import ListResponse


def read_many(
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: LabelFilterDep,
) -> ListResponse[LabelRead]:
    return router_read_many(
        db=db,
        db_model_class=Label,
        authorized_project_id=None,
        with_search=None,
        facets=None,
        aliases=None,
        apply_filter_query_operations=None,
        apply_data_query_operations=None,
        pagination_request=pagination_request,
        response_schema_class=LabelRead,
        name_to_facet_query_params=None,
        filter_model=filter_model,
    )


def read_one(id_: uuid.UUID, db: SessionDep) -> LabelRead:
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=Label,
        authorized_project_id=None,
        response_schema_class=LabelRead,
        apply_operations=None,
    )


def create_one(measurement_label: LabelCreate, db: SessionDep) -> LabelRead:
    return router_create_one(
        db=db,
        db_model_class=Label,
        json_model=measurement_label,
        response_schema_class=LabelRead,
        authorized_project_id=None,
    )


def delete_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> LabelRead:
    one = router_read_one(
        id_=id_,
        db=db,
        db_model_class=Label,
        authorized_project_id=None,
        response_schema_class=LabelRead,
        apply_operations=None,
    )
    router_delete_one(
        id_=id_,
        db=db,
        db_model_class=Label,
        authorized_project_id=None,
    )
    return one


def get_labels_to_ids(db: Session, scheme: LabelScheme, labels: set[str]) -> dict[str, uuid.UUID]:
    labels_to_id = {}
    if labels:
        query = sa.select(Label.pref_label, Label.id).where(
            sa.and_(Label.pref_label.in_(labels), Label.scheme == scheme)
        )
        labels_to_id = {row.pref_label: row.id for row in db.execute(query)}
        if len(labels_to_id) != len(labels):
            invalid_labels = sorted(labels.difference(labels_to_id))
            msg = f"Invalid labels for scheme {scheme}: {invalid_labels!r}"
            raise ApiError(
                message=msg,
                error_code=ApiErrorCode.INVALID_REQUEST,
                http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            )
    return labels_to_id
