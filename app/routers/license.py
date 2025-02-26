import sqlalchemy as sa
from fastapi import APIRouter

from app.db.model import License
from app.dependencies import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.routers.types import ListResponse, PaginationResponse
from app.schemas.base import LicenseCreate, LicenseRead

router = APIRouter(
    prefix="/license",
    tags=["license"],
)


@router.get("/", response_model=ListResponse[LicenseRead])
def read_licenses(
    db: SessionDep,
    pagination_request: PaginationQuery,
):
    query = sa.select(License)

    data = db.execute(
        query.offset(pagination_request.page * pagination_request.page_size).limit(
            pagination_request.page_size
        )
    ).scalars()

    total_items = db.execute(query.with_only_columns(sa.func.count())).scalar_one()

    response = ListResponse[LicenseRead](
        data=data,
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )

    return response


@router.get("/{id_}", response_model=LicenseRead)
def read_license(id_: int, db: SessionDep):
    with ensure_result(error_message="License not found"):
        row = db.query(License).filter(License.id == id_).one()
    return LicenseRead.model_validate(row)


@router.post("/", response_model=LicenseRead)
def create_license(license: LicenseCreate, db: SessionDep):
    row = License(name=license.name, description=license.description, label=license.label)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
