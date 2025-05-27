import uuid

import app.queries.common
from app.db.model import Species
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.common import SpeciesFilterDep
from app.schemas.base import SpeciesCreate, SpeciesRead
from app.schemas.types import ListResponse


def read_one(
    *,
    db: SessionDep,
    id_: uuid.UUID,
) -> SpeciesRead:
    return app.queries.common.router_read_one(
        id_=id_,
        db=db,
        db_model_class=Species,
        authorized_project_id=None,
        response_schema_class=SpeciesRead,
        apply_operations=None,
    )


def create_one(
    *,
    db: SessionDep,
    species: SpeciesCreate,
    user_context: AdminContextDep,
) -> SpeciesRead:
    return app.queries.common.router_create_one(
        db=db,
        db_model_class=Species,
        user_context=user_context,
        json_model=species,
        response_schema_class=SpeciesRead,
    )


def read_many(
    *,
    db: SessionDep,
    pagination_request: PaginationQuery,
    species_filter: SpeciesFilterDep,
) -> ListResponse[SpeciesRead]:
    return app.queries.common.router_read_many(
        db=db,
        db_model_class=Species,
        authorized_project_id=None,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=None,
        apply_filter_query_operations=None,
        apply_data_query_operations=None,
        pagination_request=pagination_request,
        response_schema_class=SpeciesRead,
        name_to_facet_query_params=None,
        filter_model=species_filter,
    )
