import uuid

import openai
import sqlalchemy as sa
from sqlalchemy.orm import joinedload, raiseload

import app.queries.common
from app.config import settings
from app.db.model import Strain
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.common import StrainFilterDep
from app.queries.factory import query_params_factory
from app.schemas.species import StrainCreate, StrainRead
from app.schemas.types import ListResponse


def _load(query: sa.Select):
    return query.options(
        joinedload(Strain.created_by),
        joinedload(Strain.updated_by),
        raiseload("*"),
    )


def read_many(
    *,
    db: SessionDep,
    pagination_request: PaginationQuery,
    strain_filter: StrainFilterDep,
    semantic_search: str | None = None,
) -> ListResponse[StrainRead]:
    embedding = None

    if semantic_search is not None:
        if settings.OPENAI_API_KEY is None:
            message = "OpenAI API key is not configured."
            raise ValueError(message)

        # Generate embedding using OpenAI API
        openai_api_key = settings.OPENAI_API_KEY.get_secret_value()
        client = openai.OpenAI(api_key=openai_api_key)
        response = client.embeddings.create(model="text-embedding-3-small", input=semantic_search)

        # Set the generated embedding
        embedding = response.data[0].embedding

    facet_keys = filter_keys = [
        "created_by",
        "updated_by",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=Strain,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases={},
    )
    return app.queries.common.router_read_many(
        db=db,
        db_model_class=Strain,
        authorized_project_id=None,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=None,
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
        authorized_project_id=None,
        response_schema_class=StrainRead,
        apply_operations=_load,
    )


def create_one(
    json_model: StrainCreate, db: SessionDep, user_context: AdminContextDep
) -> StrainRead:
    if settings.OPENAI_API_KEY is None:
        message = "OpenAI API key is not configured."
        raise ValueError(message)

    openai_api_key = settings.OPENAI_API_KEY.get_secret_value()

    # Generate embedding using OpenAI API
    client = openai.OpenAI(api_key=openai_api_key)
    response = client.embeddings.create(model="text-embedding-3-small", input=json_model.name)

    # Set the generated embedding
    json_model.embedding = response.data[0].embedding

    return app.queries.common.router_create_one(
        db=db,
        db_model_class=Strain,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=StrainRead,
        apply_operations=_load,
    )
