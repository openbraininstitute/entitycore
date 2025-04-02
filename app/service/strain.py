import uuid
from typing import cast

import sqlalchemy as sa

from app.db.model import Strain
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.filters.common import StrainFilterDep
from app.schemas.base import StrainCreate, StrainRead
from app.schemas.types import ListResponse, PaginationResponse


def read_many(
    db: SessionDep,
    pagination_request: PaginationQuery,
    strain_filter: StrainFilterDep,
) -> ListResponse[StrainRead]:
    query = sa.select(Strain)
    query = strain_filter.filter(query)
    total_items = db.execute(query.with_only_columns(sa.func.count(Strain.id))).scalar_one()

    query = strain_filter.sort(query)
    data = db.execute(
        query.offset(pagination_request.offset).limit(pagination_request.page_size)
    ).scalars()

    response = ListResponse[StrainRead](
        data=cast("list[StrainRead]", data),
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )

    return response


def read_one(id_: uuid.UUID, db: SessionDep) -> StrainRead:
    with ensure_result(error_message="Strain not found"):
        stmt = sa.select(Strain).filter(Strain.id == id_)
        row = db.execute(stmt).scalar_one()
    return StrainRead.model_validate(row)


def create_one(strain: StrainCreate, db: SessionDep) -> StrainRead:
    row = Strain(name=strain.name, taxonomy_id=strain.taxonomy_id, species_id=strain.species_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return StrainRead.model_validate(row)
