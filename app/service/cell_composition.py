import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload, selectinload

from app.db.model import (
    CellComposition,
    Contribution,
    Person,
)
from app.dependencies.auth import UserContextDep
from app.dependencies.common import PaginationQuery, SearchDep
from app.dependencies.db import SessionDep
from app.filters.cell_composition import CellCompositionFilterDep
from app.queries.common import router_read_many, router_read_one
from app.queries.factory import query_params_factory
from app.schemas.cell_composition import (
    CellCompositionRead,
)
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(query: sa.Select):
    return query.options(
        joinedload(CellComposition.brain_region),
        joinedload(CellComposition.species, innerjoin=True),
        joinedload(CellComposition.created_by),
        joinedload(CellComposition.updated_by),
        selectinload(CellComposition.assets),
        selectinload(CellComposition.contributions).joinedload(Contribution.agent),
        selectinload(CellComposition.contributions).joinedload(Contribution.role),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> CellCompositionRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=CellComposition,
        user_context=user_context,
        response_schema_class=CellCompositionRead,
        apply_operations=_load,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> CellCompositionRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=CellComposition,
        user_context=None,
        response_schema_class=CellCompositionRead,
        apply_operations=_load,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: CellCompositionFilterDep,
    with_search: SearchDep,
) -> ListResponse[CellCompositionRead]:
    aliases: Aliases = {
        Person: {
            "created_by": aliased(Person, flat=True),
            "updated_by": aliased(Person, flat=True),
        }
    }

    facet_keys = []
    filter_keys = ["created_by", "updated_by"]

    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=CellComposition,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )

    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=CellComposition,
        with_search=with_search,
        with_in_brain_region=None,
        facets=None,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=CellCompositionRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
        name_to_facet_query_params=name_to_facet_query_params,
    )
