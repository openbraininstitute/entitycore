import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from fastapi import HTTPException
from sqlalchemy.orm import aliased, joinedload, raiseload

from app.db.auth import constrain_to_accessible_entities
from app.db.model import (
    Agent,
    Entity,
    ETypeClassification,
)
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.classification import ETypeClassificationFilterDep
from app.logger import L
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.queries.factory import query_params_factory
from app.schemas.classification import (
    ETypeClassificationCreate,
    ETypeClassificationRead,
)
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(query: sa.Select):
    return query.options(
        joinedload(ETypeClassification.created_by),
        joinedload(ETypeClassification.updated_by),
        raiseload("*"),
    )


def create_one(
    db: SessionDep,
    json_model: ETypeClassificationCreate,
    user_context: UserContextWithProjectIdDep,
) -> ETypeClassificationRead:
    stmt = constrain_to_accessible_entities(
        sa.select(sa.func.count(Entity.id)).where(Entity.id == json_model.entity_id),
        user_context.project_id,
    )
    if db.execute(stmt).scalar_one() == 0:
        L.warning("Attempting to create an annotation for an entity inaccessible to user")
        raise HTTPException(status_code=403, detail=f"Cannot access entity {json_model.entity_id}")

    if not json_model.authorized_public:
        L.warning("Attempting to create a private classification, which is not supported.")
        raise HTTPException(
            status_code=400,
            detail="Private classifications are not supported. Use authorized_public=True",
        )
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=ETypeClassification,
        response_schema_class=ETypeClassificationRead,
        apply_operations=_load,
    )


def read_one(
    db: SessionDep,
    id_: uuid.UUID,
    user_context: UserContextDep,
) -> ETypeClassificationRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=ETypeClassification,
        authorized_project_id=user_context.project_id,
        response_schema_class=ETypeClassificationRead,
        apply_operations=_load,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> ETypeClassificationRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=ETypeClassification,
        authorized_project_id=None,
        response_schema_class=ETypeClassificationRead,
        apply_operations=_load,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: ETypeClassificationFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
) -> ListResponse[ETypeClassificationRead]:
    created_by_alias = aliased(Agent, flat=True)
    updated_by_alias = aliased(Agent, flat=True)
    aliases: Aliases = {
        Agent: {
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
        db_model_class=ETypeClassification,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=ETypeClassification,
        with_search=with_search,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=ETypeClassificationRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
        with_in_brain_region=None,
    )
