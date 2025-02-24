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


@router.get("/{organization_id}", response_model=OrganizationRead)
def read_organization(organization_id: int, db: SessionDep):
    with ensure_result(error_message="Organization not found"):
        row = db.query(Organization).filter(Organization.id == organization_id).one()
    return row


@router.post("/", response_model=OrganizationRead)
def create_organization(organization: OrganizationCreate, db: SessionDep):
    db_organization = Organization(**organization.model_dump())
    db.add(db_organization)
    db.commit()
    db.refresh(db_organization)
    return db_organization
