import sqlalchemy as sa
from fastapi import APIRouter

from app.db.model import Organization
from app.dependencies import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.routers.types import ListResponse, PaginationResponse
from app.schemas.agent import OrganizationCreate, OrganizationRead

router = APIRouter(
    prefix="/organization",
    tags=["organization"],
)


@router.get("/", response_model=ListResponse[OrganizationRead])
def read_organizations(
    db: SessionDep,
    pagination_request: PaginationQuery,
):
    query = sa.select(Organization)

    data = db.execute(
        query.offset(pagination_request.page * pagination_request.page_size).limit(
            pagination_request.page_size
        )
    ).scalars()

    total_items = db.execute(query.with_only_columns(sa.func.count())).scalar_one()

    response = ListResponse[OrganizationRead](
        data=data,
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )

    return response


@router.get("/{id_}", response_model=OrganizationRead)
def read_organization(id_: int, db: SessionDep):
    with ensure_result(error_message="Organization not found"):
        row = db.query(Organization).filter(Organization.id == id_).one()
    return OrganizationRead.model_validate(row)


@router.post("/", response_model=OrganizationRead)
def create_organization(organization: OrganizationCreate, db: SessionDep):
    row = Organization(**organization.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
