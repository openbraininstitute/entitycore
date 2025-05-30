import uuid

import sqlalchemy as sa

import app.queries.common
from app.db.model import Role
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.schemas.role import RoleCreate, RoleRead
from app.schemas.types import ListResponse, PaginationResponse


def read_many(db: SessionDep, pagination_request: PaginationQuery) -> ListResponse[RoleRead]:
    query = sa.select(Role)

    data = (
        db.execute(query.offset(pagination_request.offset).limit(pagination_request.page_size))
        .scalars()
        .all()
    )

    total_items = db.execute(query.with_only_columns(sa.func.count(Role.id))).scalar_one()

    response = ListResponse[RoleRead](
        data=[RoleRead.model_validate(d) for d in data],
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )

    return response


def read_one(id_: uuid.UUID, db: SessionDep) -> RoleRead:
    with ensure_result(error_message="Role not found"):
        stmt = sa.select(Role).filter(Role.id == id_)
        row = db.execute(stmt).scalar_one()
    return RoleRead.model_validate(row)


def create_one(json_model: RoleCreate, db: SessionDep, user_context: AdminContextDep) -> RoleRead:
    return app.queries.common.router_create_one(
        db=db,
        db_model_class=Role,
        json_model=json_model,
        response_schema_class=RoleRead,
        user_context=user_context,
    )
