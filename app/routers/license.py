import sqlalchemy as sa
from fastapi import APIRouter

from app.db.model import License
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.schemas.base import LicenseCreate, LicenseRead
from app.schemas.types import ListResponse, PaginationResponse

router = APIRouter(
    prefix="/license",
    tags=["license"],
)


@router.get("")
def read_licenses(
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


@router.get("/{id_}", response_model=LicenseRead)
def read_license(id_: int, db: SessionDep):
    with ensure_result(error_message="License not found"):
        stmt = sa.select(License).filter(License.id == id_)
        row = db.execute(stmt).scalar_one()
    return LicenseRead.model_validate(row)


@router.post("", response_model=LicenseRead)
def create_license(license: LicenseCreate, db: SessionDep):
    row = License(name=license.name, description=license.description, label=license.label)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
