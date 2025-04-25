import uuid

import sqlalchemy as sa

from app.db.auth import constrain_to_accessible_entities
from app.db.model import IonChannelModel
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.schemas.ion_channel_model import IonChannelModelCreate, IonChannelModelRead
from app.schemas.types import ListResponse, PaginationResponse


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
) -> ListResponse[IonChannelModelRead]:
    query = constrain_to_accessible_entities(
        sa.select(IonChannelModel),
        user_context.project_id,
    )

    data = db.execute(
        query.offset(pagination_request.offset).limit(pagination_request.page_size)
    ).scalars()

    total_items = db.execute(
        query.with_only_columns(sa.func.count(IonChannelModel.id))
    ).scalar_one()

    response = ListResponse[IonChannelModelRead](
        data=[IonChannelModelRead.model_validate(row) for row in data],
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
) -> IonChannelModelRead:
    with ensure_result(error_message="IonChannelModel not found"):
        stmt = constrain_to_accessible_entities(
            sa.select(IonChannelModel).filter(IonChannelModel.id == id_),
            user_context.project_id,
        )
        row = db.execute(stmt).scalar_one()

    return IonChannelModelRead.model_validate(row)


def create_one(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    ion_channel_model: IonChannelModelCreate,
) -> IonChannelModelRead:
    row = IonChannelModel(**ion_channel_model.model_dump(exclude_unset=True))
    row.project_id = user_context.project_id

    db.add(row)
    db.commit()
    db.refresh(row)

    return IonChannelModelRead.model_validate(row)
