import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload, selectinload

from app.db.model import (
    Agent,
    Circuit,
    Contribution,
    Subject,
)
from app.dependencies.auth import AdminContextDep, UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.circuit import CircuitFilterDep
from app.queries.common import (
    router_create_one,
    router_delete_one,
    router_read_many,
    router_read_one,
)
from app.queries.factory import query_params_factory
from app.schemas.circuit import (
    CircuitCreate,
    CircuitRead,
)
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(query: sa.Select):
    return query.options(
        joinedload(Circuit.license),
        joinedload(Circuit.subject).joinedload(Subject.species),
        joinedload(Circuit.brain_region),
        joinedload(Circuit.created_by),
        joinedload(Circuit.updated_by),
        selectinload(Circuit.contributions).joinedload(Contribution.agent),
        selectinload(Circuit.contributions).joinedload(Contribution.role),
        selectinload(Circuit.assets),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> CircuitRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=Circuit,
        authorized_project_id=user_context.project_id,
        response_schema_class=CircuitRead,
        apply_operations=_load,
    )


def create_one(
    db: SessionDep,
    json_model: CircuitCreate,
    user_context: UserContextWithProjectIdDep,
) -> CircuitRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=Circuit,
        response_schema_class=CircuitRead,
        apply_operations=_load,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: CircuitFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[CircuitRead]:
    agent_alias = aliased(Agent, flat=True)
    created_by_alias = aliased(Agent, flat=True)
    updated_by_alias = aliased(Agent, flat=True)

    aliases: Aliases = {
        Agent: {
            "contribution": agent_alias,
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
        }
    }
    facet_keys = filter_keys = [
        "brain_region",
        "created_by",
        "updated_by",
        "contribution",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=Circuit,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=Circuit,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=CircuitRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
    )


def delete_one(
    _: AdminContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> CircuitRead:
    one = router_read_one(
        id_=id_,
        db=db,
        db_model_class=Circuit,
        authorized_project_id=None,
        response_schema_class=CircuitRead,
        apply_operations=_load,
    )
    router_delete_one(
        id_=id_,
        db=db,
        db_model_class=Circuit,
        authorized_project_id=None,  # already validated
    )
    return one
