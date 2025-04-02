import uuid

import sqlalchemy as sa
from fastapi import APIRouter

from app.db.auth import constrain_to_accessible_entities
from app.db.model import ExperimentalSynapsesPerConnection
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.schemas.density import (
    ExperimentalSynapsesPerConnectionCreate,
    ExperimentalSynapsesPerConnectionRead,
)
from app.schemas.types import ListResponse, PaginationResponse

router = APIRouter(
    prefix="/experimental-synapses-per-connection",
    tags=["experimental-synapses-per-connection"],
)


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
) -> ListResponse[ExperimentalSynapsesPerConnectionRead]:
    query = constrain_to_accessible_entities(
        sa.select(ExperimentalSynapsesPerConnection), user_context.project_id
    )

    data = db.execute(
        query.offset(pagination_request.offset).limit(pagination_request.page_size)
    ).scalars()

    total_items = db.execute(
        query.with_only_columns(sa.func.count(ExperimentalSynapsesPerConnection.id))
    ).scalar_one()

    response = ListResponse[ExperimentalSynapsesPerConnectionRead](
        data=data,
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )

    return response


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> ExperimentalSynapsesPerConnectionRead:
    with ensure_result(error_message="ExperimentalSynapsesPerConnection not found"):
        stmt = constrain_to_accessible_entities(
            sa.select(ExperimentalSynapsesPerConnection).filter(
                ExperimentalSynapsesPerConnection.id == id_
            ),
            user_context.project_id,
        )
        row = db.execute(stmt).scalar_one()

    return ExperimentalSynapsesPerConnectionRead.model_validate(row)


def create_one(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    density: ExperimentalSynapsesPerConnectionCreate,
) -> ExperimentalSynapsesPerConnectionRead:
    dump = density.model_dump()

    row = ExperimentalSynapsesPerConnection(**dump, authorized_project_id=user_context.project_id)
    db.add(row)
    db.commit()
    db.refresh(row)

    return ExperimentalSynapsesPerConnectionRead.model_validate(row)
