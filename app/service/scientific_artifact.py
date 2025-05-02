import uuid
from typing import Annotated

import sqlalchemy as sa
from fastapi import Query
from sqlalchemy.orm import joinedload, selectinload, raiseload

from app.db.auth import constrain_to_accessible_entities
from app.db.model import ScientificArtifact, Contribution, Agent, Role, License
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import PaginationQuery, SearchDep, FacetsDep
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.filters.base import BaseFilter
from app.queries.common import router_create_one, router_read_many
from app.schemas.scientific_artifact import ScientificArtifactCreate, ScientificArtifactRead
from app.schemas.types import ListResponse

def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    expand: Annotated[set[str] | None, Query()] = None,
) -> ScientificArtifactRead:
    """Read a single ScientificArtifact by ID."""
    with ensure_result(error_message="ScientificArtifact not found"):
        query = constrain_to_accessible_entities(
            sa.select(ScientificArtifact), user_context.project_id
        ).filter(ScientificArtifact.id == id_)

        query = (
            query.options(joinedload(ScientificArtifact.license))
            .options(
                selectinload(ScientificArtifact.contributions).selectinload(Contribution.agent)
            )
            .options(
                selectinload(ScientificArtifact.contributions).selectinload(Contribution.role)
            )
            .options(selectinload(ScientificArtifact.assets))
            .options(raiseload("*"))
        )

        row = db.execute(query).unique().scalar_one()

    return ScientificArtifactRead.model_validate(row)

def create_one(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    artifact: ScientificArtifactCreate,
) -> ScientificArtifactRead:
    """Create a single ScientificArtifact."""
    return router_create_one(
        db=db,
        db_model_class=ScientificArtifact,
        authorized_project_id=user_context.project_id,
        json_model=artifact,
        response_schema_class=ScientificArtifactRead,
    )

def read_many(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    search: SearchDep,
    with_facets: FacetsDep,
) -> ListResponse[ScientificArtifactRead]:
    """Read multiple ScientificArtifacts with pagination and filtering."""
    name_to_facet_query_params = {
        "contribution": {
            "id": Agent.id,
            "label": Agent.pref_label,
            "type": Agent.type,
        },
    }

    def data_query_ops(q):
        return (
            q.options(joinedload(ScientificArtifact.license))
            .options(
                selectinload(ScientificArtifact.contributions).selectinload(Contribution.agent)
            )
            .options(
                selectinload(ScientificArtifact.contributions).selectinload(Contribution.role)
            )
            .options(selectinload(ScientificArtifact.assets))
            .options(raiseload("*"))
        )

    def filter_query_ops(q):
        return (
            q.outerjoin(Contribution, ScientificArtifact.id == Contribution.entity_id)
            .outerjoin(Agent, Contribution.agent_id == Agent.id)
        )

    return router_read_many(
        db=db,
        db_model_class=ScientificArtifact,
        authorized_project_id=user_context.project_id,
        with_search=search,
        facets=with_facets,
        aliases=None,
        apply_filter_query_operations=filter_query_ops,
        apply_data_query_operations=data_query_ops,
        pagination_request=pagination_request,
        response_schema_class=ScientificArtifactRead,
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=BaseFilter(),
    )
