import uuid

import openai
import sqlalchemy as sa

import app.queries.common
from app.config import settings
from app.db.model import BrainRegion
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.filters.brain_region import BrainRegionFilterDep
from app.schemas.base import BrainRegionRead
from app.schemas.types import ListResponse


def read_many(
    *,
    db: SessionDep,
    pagination_request: PaginationQuery,
    brain_region_filter: BrainRegionFilterDep,
    semantic_search: str | None = None,
) -> ListResponse[BrainRegionRead]:
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

    return app.queries.common.router_read_many(
        db=db,
        db_model_class=BrainRegion,
        authorized_project_id=None,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=None,
        apply_filter_query_operations=None,
        apply_data_query_operations=None,
        pagination_request=pagination_request,
        response_schema_class=BrainRegionRead,
        name_to_facet_query_params=None,
        filter_model=brain_region_filter,
        embedding=embedding,
    )


def read_one(db: SessionDep, id_: uuid.UUID) -> BrainRegionRead:
    with ensure_result(error_message="Brain region not found"):
        stmt = sa.select(BrainRegion).filter(BrainRegion.id == id_)
        row = db.execute(stmt).scalar_one()
    return BrainRegionRead.model_validate(row)
