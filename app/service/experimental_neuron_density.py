import uuid

import sqlalchemy as sa

from app.db.auth import constrain_to_accessible_entities
from app.db.model import ExperimentalNeuronDensity
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.schemas.density import ExperimentalNeuronDensityCreate, ExperimentalNeuronDensityRead
from app.schemas.types import ListResponse, PaginationResponse


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
) -> ListResponse[ExperimentalNeuronDensityRead]:
    query = constrain_to_accessible_entities(
        sa.select(ExperimentalNeuronDensity), user_context.project_id
    )

    data = db.execute(
        query.offset(pagination_request.offset).limit(pagination_request.page_size)
    ).scalars()

    total_items = db.execute(
        query.with_only_columns(sa.func.count(ExperimentalNeuronDensity.id))
    ).scalar_one()

    response = ListResponse[ExperimentalNeuronDensityRead](
        data=[ExperimentalNeuronDensityRead.model_validate(row) for row in data],
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
) -> ExperimentalNeuronDensityRead:
    with ensure_result(error_message="ExperimentalNeuronDensity not found"):
        stmt = constrain_to_accessible_entities(
            sa.select(ExperimentalNeuronDensity).filter(ExperimentalNeuronDensity.id == id_),
            user_context.project_id,
        )
        row = db.execute(stmt).scalar_one()

    return ExperimentalNeuronDensityRead.model_validate(row)


def create_one(
    user_context: UserContextWithProjectIdDep,
    density: ExperimentalNeuronDensityCreate,
    db: SessionDep,
) -> ExperimentalNeuronDensityRead:
    dump = density.model_dump()

    row = ExperimentalNeuronDensity(**dump, authorized_project_id=user_context.project_id)
    db.add(row)
    db.commit()
    db.refresh(row)

    return ExperimentalNeuronDensityRead.model_validate(row)
