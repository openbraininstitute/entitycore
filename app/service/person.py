import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload

from app.db.model import Person
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.person import PersonFilterDep
from app.queries.common import (
    router_admin_delete_one,
    router_create_one,
    router_read_many,
    router_read_one,
    router_update_one,
)
from app.queries.factory import query_params_factory
from app.schemas.agent import PersonAdminUpdate, PersonCreate, PersonRead
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(query: sa.Select):
    return query.options(
        joinedload(Person.created_by, innerjoin=True),
        joinedload(Person.updated_by, innerjoin=True),
        raiseload("*"),
    )


def read_many(
    *,
    db: SessionDep,
    pagination_request: PaginationQuery,
    person_filter: PersonFilterDep,
) -> ListResponse[PersonRead]:
    created_by_alias = aliased(Person, flat=True)
    updated_by_alias = aliased(Person, flat=True)

    aliases: Aliases = {
        Person: {
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
        },
    }

    filter_keys = [
        "created_by",
        "updated_by",
    ]

    _, filter_joins = query_params_factory(
        db_model_class=Person,
        filter_keys=filter_keys,
        facet_keys=[],
        aliases=aliases,
    )

    return router_read_many(
        db=db,
        db_model_class=Person,
        authorized_project_id=None,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=aliases,  # Use the main alias for sorting
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        pagination_request=pagination_request,
        response_schema_class=PersonRead,
        name_to_facet_query_params=None,
        filter_model=person_filter,
        filter_joins=filter_joins,
    )


admin_read_many = read_many


def read_one(id_: uuid.UUID, db: SessionDep) -> PersonRead:
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=Person,
        user_context=None,
        response_schema_class=PersonRead,
        apply_operations=_load,
    )


def admin_read_one(db: SessionDep, id_: uuid.UUID) -> PersonRead:
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=Person,
        user_context=None,
        response_schema_class=PersonRead,
        apply_operations=_load,
    )


def create_one(person: PersonCreate, db: SessionDep, user_context: AdminContextDep) -> PersonRead:
    return router_create_one(
        db=db,
        db_model_class=Person,
        json_model=person,
        response_schema_class=PersonRead,
        user_context=user_context,
        apply_operations=_load,
    )


def update_one(
    db: SessionDep,
    user_context: AdminContextDep,
    id_: uuid.UUID,
    json_model: PersonAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> PersonRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=Person,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=PersonRead,
        apply_operations=_load,
        check_authorized_project=False,
    )


admin_update_one = update_one


def delete_one(
    db: SessionDep,
    id_: uuid.UUID,
    user_context: AdminContextDep,  # noqa: ARG001
) -> DeleteResponse:
    return router_admin_delete_one(
        id_=id_,
        db=db,
        db_model_class=Person,
    )
