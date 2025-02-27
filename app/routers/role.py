import sqlalchemy as sa
from fastapi import APIRouter

from app.db.model import Role
from app.dependencies import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.routers.types import ListResponse, PaginationResponse
from app.schemas.role import RoleCreate, RoleRead

router = APIRouter(
    prefix="/role",
    tags=["role"],
)


@router.get("/", response_model=ListResponse[RoleRead])
def read_roles(db: SessionDep, pagination_request: PaginationQuery):
    query = sa.select(Role)

    data = db.execute(
        query.offset(pagination_request.page * pagination_request.page_size).limit(
            pagination_request.page_size
        )
    ).scalars()

    total_items = db.execute(query.with_only_columns(sa.func.count())).scalar_one()

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


@router.get("/{id_}", response_model=RoleRead)
def read_role(id_: int, db: SessionDep):
    with ensure_result(error_message="Role not found"):
        stmt = sa.select(Role).filter(Role.id == id_)
        row = db.execute(stmt).scalar_one()
    return RoleRead.model_validate(row)


@router.post("/", response_model=RoleRead)
def create_role(role: RoleCreate, db: SessionDep):
    row = Role(name=role.name, role_id=role.role_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
