import uuid

import sqlalchemy as sa

from app.db.model import Role
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


def create_one(role: RoleCreate, db: SessionDep) -> RoleRead:
    row = Role(name=role.name, role_id=role.role_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return RoleRead.model_validate(row)
