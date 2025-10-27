import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload, selectinload

from app.db.model import (
    Agent,
    Circuit,
    CircuitExtractionConfig,
)
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.circuit_extraction_config import CircuitExtractionConfigFilterDep
from app.queries.common import (
    router_create_one,
    router_delete_one,
    router_read_many,
    router_read_one,
    router_update_one,
)
from app.queries.factory import query_params_factory
from app.schemas.circuit_extraction_config import (
    CircuitExtractionConfigAdminUpdate,
    CircuitExtractionConfigCreate,
    CircuitExtractionConfigRead,
    CircuitExtractionConfigUserUpdate,
)
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(query: sa.Select):
    return query.options(
        joinedload(CircuitExtractionConfig.created_by),
        joinedload(CircuitExtractionConfig.updated_by),
        joinedload(CircuitExtractionConfig.circuit),
        selectinload(CircuitExtractionConfig.assets),
        selectinload(CircuitExtractionConfig.contributions),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> CircuitExtractionConfigRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=CircuitExtractionConfig,
        user_context=user_context,
        response_schema_class=CircuitExtractionConfigRead,
        apply_operations=_load,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> CircuitExtractionConfigRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=CircuitExtractionConfig,
        user_context=None,
        response_schema_class=CircuitExtractionConfigRead,
        apply_operations=_load,
    )


def create_one(
    db: SessionDep,
    json_model: CircuitExtractionConfigCreate,
    user_context: UserContextWithProjectIdDep,
) -> CircuitExtractionConfigRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=CircuitExtractionConfig,
        response_schema_class=CircuitExtractionConfigRead,
        apply_operations=_load,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: CircuitExtractionConfigUserUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> CircuitExtractionConfigRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=CircuitExtractionConfig,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=CircuitExtractionConfigRead,
        apply_operations=_load,
    )


def admin_update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: CircuitExtractionConfigAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> CircuitExtractionConfigRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=CircuitExtractionConfig,
        user_context=None,
        json_model=json_model,
        response_schema_class=CircuitExtractionConfigRead,
        apply_operations=_load,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: CircuitExtractionConfigFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[CircuitExtractionConfigRead]:
    agent_alias = aliased(Agent, flat=True)
    created_by_alias = aliased(Agent, flat=True)
    updated_by_alias = aliased(Agent, flat=True)
    circuit_alias = aliased(Circuit, flat=True)

    aliases: Aliases = {
        Agent: {
            "contribution": agent_alias,
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
        },
        Circuit: circuit_alias,
    }
    facet_keys = filter_keys = [
        "created_by",
        "updated_by",
        "contribution",
        "circuit",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=CircuitExtractionConfig,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=CircuitExtractionConfig,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=CircuitExtractionConfigRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
    )


def delete_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> DeleteResponse:
    return router_delete_one(
        id_=id_,
        db=db,
        db_model_class=CircuitExtractionConfig,
        user_context=user_context,
    )
