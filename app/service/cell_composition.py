import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload, selectinload

from app.db.model import (
    CellComposition,
    Contribution,
    Person,
)
from app.dependencies.auth import AdminContextDep, UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import PaginationQuery, SearchDep
from app.dependencies.db import SessionDep
from app.filters.cell_composition import CellCompositionFilterDep
from app.queries.common import (
    router_create_one,
    router_read_many,
    router_read_one,
    router_update_one,
    router_user_delete_one,
)
from app.queries.factory import query_params_factory
from app.schemas.cell_composition import (
    CellCompositionAdminUpdate,
    CellCompositionCreate,
    CellCompositionRead,
    CellCompositionUserUpdate,
)
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load_from_db(query: sa.Select):
    return query.options(
        joinedload(CellComposition.brain_region),
        joinedload(CellComposition.species, innerjoin=True),
        joinedload(CellComposition.strain),
        joinedload(CellComposition.created_by),
        joinedload(CellComposition.updated_by),
        selectinload(CellComposition.assets),
        selectinload(CellComposition.contributions).joinedload(Contribution.agent),
        selectinload(CellComposition.contributions).joinedload(Contribution.role),
        raiseload("*"),
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    json_model: CellCompositionCreate,
) -> CellCompositionRead:
    return router_create_one(
        db=db,
        user_context=user_context,
        db_model_class=CellComposition,
        json_model=json_model,
        response_schema_class=CellCompositionRead,
        apply_operations=_load_from_db,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: CellCompositionUserUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> CellCompositionRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=CellComposition,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=CellCompositionRead,
        apply_operations=_load_from_db,
        check_authorized_project=True,
    )


def admin_update_one(
    user_context: AdminContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: CellCompositionAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> CellCompositionRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=CellComposition,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=CellCompositionRead,
        apply_operations=_load_from_db,
        check_authorized_project=False,
    )


def delete_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> DeleteResponse:
    return router_user_delete_one(
        id_=id_,
        db=db,
        db_model_class=CellComposition,
        user_context=user_context,
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
        apply_operations=_load_from_db,
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
        apply_operations=_load_from_db,
    )


def _read_many(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: CellCompositionFilterDep,
    with_search: SearchDep,
    check_authorized_project: bool,
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
        apply_data_query_operations=_load_from_db,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=CellCompositionRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
        name_to_facet_query_params=name_to_facet_query_params,
        check_authorized_project=check_authorized_project,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: CellCompositionFilterDep,
    with_search: SearchDep,
) -> ListResponse[CellCompositionRead]:
    return _read_many(
        user_context=user_context,
        db=db,
        pagination_request=pagination_request,
        filter_model=filter_model,
        with_search=with_search,
        check_authorized_project=True,
    )


def admin_read_many(
    user_context: AdminContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: CellCompositionFilterDep,
    with_search: SearchDep,
) -> ListResponse[CellCompositionRead]:
    return _read_many(
        user_context=user_context,
        db=db,
        pagination_request=pagination_request,
        filter_model=filter_model,
        with_search=with_search,
        check_authorized_project=False,
    )
