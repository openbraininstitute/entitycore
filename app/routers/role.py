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
def read_role(db: SessionDep, pagination_request: PaginationQuery):
    query = sa.select(Role)

    data = db.execute(
        query.offset(pagination_request.page * pagination_request.page_size).limit(
            pagination_request.page_size
        )
    ).scalars()

    total_items = db.execute(query.with_only_columns(sa.func.count())).scalar_one()

    response = ListResponse[RoleRead](
        data=data,
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )

    return response


@router.get("/{role_id}", response_model=RoleRead)
def read_person(role_id: int, db: SessionDep):
    with ensure_result(error_message="Role not found"):
        row = db.query(Role).filter(Role.id == role_id).one()
    return row


@router.post("/", response_model=RoleRead)
def create_role(role: RoleCreate, db: SessionDep):
    db_role = Role(
        name=role.name,
        role_id=role.role_id,
    )
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role
