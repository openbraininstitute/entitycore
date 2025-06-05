import uuid

import sqlalchemy as sa
from sqlalchemy.orm import joinedload, raiseload

import app.queries.common
from app.db.model import Organization
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.schemas.agent import OrganizationCreate, OrganizationRead
from app.schemas.types import ListResponse, PaginationResponse


def _load(query: sa.Select):
    return query.options(
        joinedload(Organization.created_by, innerjoin=True),
        joinedload(Organization.updated_by, innerjoin=True),
        raiseload("*"),
    )


def read_many(
    db: SessionDep,
    pagination_request: PaginationQuery,
) -> ListResponse[OrganizationRead]:
    query = sa.select(Organization)

    data = db.execute(
        query.offset(pagination_request.offset).limit(pagination_request.page_size)
    ).scalars()

    total_items = db.execute(query.with_only_columns(sa.func.count(Organization.id))).scalar_one()

    response = ListResponse[OrganizationRead](
        data=[OrganizationRead.model_validate(d) for d in data],
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )

    return response


def read_one(id_: uuid.UUID, db: SessionDep) -> OrganizationRead:
    return app.queries.common.router_read_one(
        id_=id_,
        db=db,
        db_model_class=Organization,
        authorized_project_id=None,
        response_schema_class=OrganizationRead,
        apply_operations=_load,
    )


def create_one(
    organization: OrganizationCreate, db: SessionDep, user_context: AdminContextDep
) -> OrganizationRead:
    return app.queries.common.router_create_one(
        db=db,
        db_model_class=Organization,
        json_model=organization,
        response_schema_class=OrganizationRead,
        user_context=user_context,
        apply_operations=_load,
    )
