import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload

import app.queries.common
from app.db.model import Person, Strain
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.species import StrainFilterDep
from app.queries.factory import query_params_factory
from app.schemas.routers import DeleteResponse
from app.schemas.species import StrainAdminUpdate, StrainCreate, StrainRead
from app.schemas.types import ListResponse
from app.utils.embedding import generate_embedding

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(query: sa.Select):
    return query.options(
        joinedload(Strain.created_by, innerjoin=True),
        joinedload(Strain.updated_by, innerjoin=True),
        raiseload("*"),
    )


def read_many(
    *,
    db: SessionDep,
    pagination_request: PaginationQuery,
    strain_filter: StrainFilterDep,
    semantic_search: str | None = None,
) -> ListResponse[StrainRead]:
    aliases: Aliases = {
        Person: {
            "created_by": aliased(Person, flat=True),
            "updated_by": aliased(Person, flat=True),
        }
    }

    embedding = None

    if semantic_search is not None:
        embedding = generate_embedding(semantic_search)

    facet_keys = filter_keys = [
        "created_by",
        "updated_by",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=Strain,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return app.queries.common.router_read_many(
        db=db,
        db_model_class=Strain,
        authorized_project_id=None,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=aliases,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        pagination_request=pagination_request,
        response_schema_class=StrainRead,
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=strain_filter,
        filter_joins=filter_joins,
        embedding=embedding,
    )


def read_one(id_: uuid.UUID, db: SessionDep) -> StrainRead:
    return app.queries.common.router_read_one(
        id_=id_,
        db=db,
        db_model_class=Strain,
        user_context=None,
        response_schema_class=StrainRead,
        apply_operations=_load,
    )


def admin_read_one(
    *,
    db: SessionDep,
    id_: uuid.UUID,
) -> StrainRead:
    return read_one(id_=id_, db=db)


def create_one(
    json_model: StrainCreate, db: SessionDep, user_context: AdminContextDep
) -> StrainRead:
    embedding = generate_embedding(json_model.name)

    return app.queries.common.router_create_one(
        db=db,
        db_model_class=Strain,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=StrainRead,
        apply_operations=_load,
        embedding=embedding,
    )


def update_one(
    db: SessionDep,
    user_context: AdminContextDep,  # noqa: ARG001
    id_: uuid.UUID,
    json_model: StrainAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> StrainRead:
    return app.queries.common.router_update_one(
        id_=id_,
        db=db,
        db_model_class=Strain,
        user_context=None,
        json_model=json_model,
        response_schema_class=StrainRead,
    )


def admin_update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: StrainAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> StrainRead:
    return app.queries.common.router_update_one(
        id_=id_,
        db=db,
        db_model_class=Strain,
        user_context=None,
        json_model=json_model,
        response_schema_class=StrainRead,
    )


def delete_one(
    db: SessionDep,
    id_: uuid.UUID,
    user_context: AdminContextDep,  # noqa: ARG001
) -> DeleteResponse:
    return app.queries.common.router_delete_one(
        id_=id_,
        db=db,
        db_model_class=Strain,
        user_context=None,
    )
