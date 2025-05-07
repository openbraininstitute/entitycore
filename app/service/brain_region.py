import uuid

import sqlalchemy as sa

from app.db.model import BrainRegion
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.filters.brain_region import BrainRegionFilterDep
from app.schemas.base import BrainRegionRead
from app.schemas.types import ListResponse, PaginationResponse


def read_many(
    *,
    db: SessionDep,
    pagination_request: PaginationQuery,
    brain_region_filter: BrainRegionFilterDep,
) -> ListResponse[BrainRegionRead]:
    query = sa.select(BrainRegion)
    query = brain_region_filter.filter(query)

    data = db.execute(
        query.offset(pagination_request.offset).limit(pagination_request.page_size)
    ).scalars()

    total_items = db.execute(query.with_only_columns(sa.func.count(BrainRegion.id))).scalar_one()

    response = ListResponse[BrainRegionRead](
        data=[BrainRegionRead.model_validate(d) for d in data],
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )
    return response


def read_one(db: SessionDep, id_: uuid.UUID) -> BrainRegionRead:
    with ensure_result(error_message="Brain region not found"):
        stmt = sa.select(BrainRegion).filter(BrainRegion.id == id_)
        row = db.execute(stmt).scalar_one()
    return BrainRegionRead.model_validate(row)
