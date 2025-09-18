import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload

from app.db.model import Agent, Entity, Validation
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.validation import ValidationFilterDep
from app.queries.common import (
    router_create_activity_one,
    router_delete_one,
    router_read_many,
    router_read_one,
    router_update_activity_one,
)
from app.queries.factory import query_params_factory
from app.schemas.types import ListResponse
from app.schemas.validation import (
    ValidationCreate,
    ValidationRead,
    ValidationUpdate,
)

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(query: sa.Select):
    return query.options(
        joinedload(Validation.used),
        joinedload(Validation.generated),
        joinedload(Validation.created_by, innerjoin=True),
        joinedload(Validation.updated_by, innerjoin=True),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> ValidationRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=Validation,
        user_context=user_context,
        response_schema_class=ValidationRead,
        apply_operations=_load,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> ValidationRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=Validation,
        user_context=None,
        response_schema_class=ValidationRead,
        apply_operations=_load,
    )


def create_one(
    db: SessionDep,
    json_model: ValidationCreate,
    user_context: UserContextWithProjectIdDep,
) -> ValidationRead:
    return router_create_activity_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=Validation,
        response_schema_class=ValidationRead,
        apply_operations=_load,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: ValidationFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[ValidationRead]:
    created_by_alias = aliased(Agent, flat=True)
    updated_by_alias = aliased(Agent, flat=True)
    used_alias = aliased(Entity, flat=True)
    generated_alias = aliased(Entity, flat=True)

    aliases: Aliases = {
        Agent: {
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
        },
        Entity: {
            "used": used_alias,
            "generated": generated_alias,
        },
    }
    facet_keys = []
    filter_keys = [
        "created_by",
        "updated_by",
        "used",
        "generated",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=Validation,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=Validation,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=ValidationRead,
        user_context=user_context,
        filter_joins=filter_joins,
    )


def delete_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> ValidationRead:
    one = router_read_one(
        id_=id_,
        db=db,
        db_model_class=Validation,
        user_context=user_context,
        response_schema_class=ValidationRead,
        apply_operations=_load,
    )
    router_delete_one(
        id_=id_,
        db=db,
        db_model_class=Validation,
        user_context=None,  # already validated
    )
    return one


def update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: ValidationUpdate,  # pyright: ignore [reportInvalidTypeForm]
    user_context: UserContextDep,
) -> ValidationRead:
    return router_update_activity_one(
        db=db,
        id_=id_,
        json_model=json_model,
        user_context=user_context,
        db_model_class=Validation,
        response_schema_class=ValidationRead,
        apply_operations=_load,
    )
