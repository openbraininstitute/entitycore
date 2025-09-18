import uuid

import sqlalchemy as sa
from sqlalchemy.orm import joinedload, raiseload

import app.queries.common
from app.db.model import Species
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.common import SpeciesFilterDep
from app.queries.factory import query_params_factory
from app.schemas.species import SpeciesCreate, SpeciesRead
from app.schemas.types import ListResponse
from app.utils.embedding import generate_embedding


def _load(query: sa.Select):
    return query.options(
        joinedload(Species.created_by),
        joinedload(Species.updated_by),
        raiseload("*"),
    )


def read_one(
    *,
    db: SessionDep,
    id_: uuid.UUID,
) -> SpeciesRead:
    return app.queries.common.router_read_one(
        id_=id_,
        db=db,
        db_model_class=Species,
        user_context=None,
        response_schema_class=SpeciesRead,
        apply_operations=_load,
    )


def create_one(
    *,
    db: SessionDep,
    species: SpeciesCreate,
    user_context: AdminContextDep,
) -> SpeciesRead:
    embedding = generate_embedding(species.name)

    return app.queries.common.router_create_one(
        db=db,
        db_model_class=Species,
        user_context=user_context,
        json_model=species,
        response_schema_class=SpeciesRead,
        apply_operations=_load,
        embedding=embedding,
    )


def read_many(
    *,
    db: SessionDep,
    pagination_request: PaginationQuery,
    species_filter: SpeciesFilterDep,
    semantic_search: str | None = None,
) -> ListResponse[SpeciesRead]:
    embedding = None

    if semantic_search is not None:
        embedding = generate_embedding(semantic_search)

    facet_keys = filter_keys = [
        "created_by",
        "updated_by",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=Species,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases={},
    )
    return app.queries.common.router_read_many(
        db=db,
        db_model_class=Species,
        user_context=None,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=None,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        pagination_request=pagination_request,
        response_schema_class=SpeciesRead,
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=species_filter,
        filter_joins=filter_joins,
        embedding=embedding,
    )
