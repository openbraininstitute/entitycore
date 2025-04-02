import uuid
from typing import cast

import sqlalchemy as sa

from app.db.model import MTypeClass
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.filters.common import MTypeClassFilterDep
from app.schemas.annotation import MTypeClassRead
from app.schemas.types import ListResponse, PaginationResponse


def read_many(
    db: SessionDep,
    pagination_request: PaginationQuery,
    mtype_class_filter: MTypeClassFilterDep,
) -> ListResponse[MTypeClassRead]:
    query = sa.select(MTypeClass)
    query = mtype_class_filter.filter(query)
    total_items = db.execute(query.with_only_columns(sa.func.count(MTypeClass.id))).scalar_one()

    query = mtype_class_filter.sort(query)
    data = db.execute(
        query.offset(pagination_request.offset).limit(pagination_request.page_size)
    ).scalars()

    response = ListResponse[MTypeClassRead](
        data=cast("list[MTypeClassRead]", data),
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )

    return response


def read_one(id_: uuid.UUID, db: SessionDep) -> MTypeClassRead:
    with ensure_result(error_message="MTypeClass not found"):
        stmt = sa.select(MTypeClass).filter(MTypeClass.id == id_)
        row = db.execute(stmt).scalar_one()
    return MTypeClassRead.model_validate(row)
