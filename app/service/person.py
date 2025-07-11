import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload

from app.db.model import Agent, Person
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.person import PersonFilterDep
from app.queries.common import (
    router_create_one,
    router_delete_one,
    router_read_many,
    router_read_one,
)
from app.queries.factory import query_params_factory
from app.schemas.agent import PersonCreate, PersonRead
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
    created_by_alias = aliased(Agent, flat=True)
    updated_by_alias = aliased(Agent, flat=True)

    aliases: Aliases = {
        Agent: {
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
        }
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
        aliases=aliases,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        pagination_request=pagination_request,
        response_schema_class=PersonRead,
        name_to_facet_query_params=None,
        filter_model=person_filter,
        filter_joins=filter_joins,
    )


def read_one(id_: uuid.UUID, db: SessionDep) -> PersonRead:
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=Person,
        authorized_project_id=None,
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


def delete_one(
    _: AdminContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> PersonRead:
    one = router_read_one(
        id_=id_,
        db=db,
        db_model_class=Person,
        authorized_project_id=None,
        response_schema_class=PersonRead,
        apply_operations=_load,
    )
    router_delete_one(
        id_=id_,
        db=db,
        db_model_class=Person,
        authorized_project_id=None,
    )
    return one
