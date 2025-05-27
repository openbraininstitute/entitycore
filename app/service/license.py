import uuid

import sqlalchemy as sa

from app.db.model import License
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.queries.common import router_create_one
from app.schemas.base import LicenseCreate, LicenseRead
from app.schemas.types import ListResponse, PaginationResponse


def read_many(
    db: SessionDep,
    pagination_request: PaginationQuery,
) -> ListResponse[LicenseRead]:
    query = sa.select(License)

    data = db.execute(
        query.offset(pagination_request.offset).limit(pagination_request.page_size)
    ).scalars()

    total_items = db.execute(query.with_only_columns(sa.func.count(License.id))).scalar_one()

    response = ListResponse[LicenseRead](
        data=[LicenseRead.model_validate(d) for d in data],
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )

    return response


def read_one(id_: uuid.UUID, db: SessionDep) -> LicenseRead:
    with ensure_result(error_message="License not found"):
        stmt = sa.select(License).filter(License.id == id_)
        row = db.execute(stmt).scalar_one()
    return LicenseRead.model_validate(row)


def create_one(
    license: LicenseCreate, db: SessionDep, user_context: AdminContextDep
) -> LicenseRead:
    return router_create_one(
        db=db,
        db_model_class=License,
        json_model=license,
        response_schema_class=LicenseRead,
        user_context=user_context,
    )
