import uuid
from typing import TYPE_CHECKING, Annotated

import sqlalchemy as sa
from fastapi import Body
from sqlalchemy.orm import (
    aliased,
    joinedload,
    raiseload,
)

from app.db.model import (
    Agent,
    CellMorphologyProtocol,
)
from app.db.utils import CELL_MORPHOLOGY_GENERATION_TYPE_TO_CLASS
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import FacetsDep, PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.cell_morphology_protocol import CellMorphologyProtocolFilterDep
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.queries.factory import query_params_factory
from app.schemas.cell_morphology_protocol import (
    CellMorphologyProtocolCreate,
    CellMorphologyProtocolRead,
    CellMorphologyProtocolReadAdapter,
)
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load_from_db(query: sa.Select) -> sa.Select:
    """Return the query with the required options to load the data."""
    return query.options(
        joinedload(CellMorphologyProtocol.created_by, innerjoin=True),
        joinedload(CellMorphologyProtocol.updated_by, innerjoin=True),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> CellMorphologyProtocolRead:
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=CellMorphologyProtocol,
        authorized_project_id=user_context.project_id,
        response_schema_class=CellMorphologyProtocolReadAdapter,
        apply_operations=_load_from_db,
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    json_model: Annotated[CellMorphologyProtocolCreate, Body()],
) -> CellMorphologyProtocolRead:
    db_model_class = CELL_MORPHOLOGY_GENERATION_TYPE_TO_CLASS[json_model.generation_type]
    return router_create_one(
        db=db,
        user_context=user_context,
        db_model_class=db_model_class,
        json_model=json_model,
        response_schema_class=CellMorphologyProtocolReadAdapter,
        apply_operations=_load_from_db,
    )


def read_many(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: CellMorphologyProtocolFilterDep,
    with_facets: FacetsDep,
) -> ListResponse[CellMorphologyProtocolRead]:
    agent_alias = aliased(Agent, flat=True)
    created_by_alias = aliased(Agent, flat=True)
    updated_by_alias = aliased(Agent, flat=True)
    aliases: Aliases = {
        Agent: {
            "contribution": agent_alias,
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
        },
    }
    facet_keys = [
        "created_by",
        "updated_by",
    ]
    filter_keys = [
        "created_by",
        "updated_by",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=CellMorphologyProtocol,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        db_model_class=CellMorphologyProtocol,
        authorized_project_id=user_context.project_id,
        with_search=None,
        with_in_brain_region=None,
        facets=with_facets,
        aliases=aliases,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load_from_db,
        pagination_request=pagination_request,
        response_schema_class=CellMorphologyProtocolReadAdapter,
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=filter_model,
        filter_joins=filter_joins,
    )
