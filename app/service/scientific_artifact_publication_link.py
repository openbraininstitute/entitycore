import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from fastapi import HTTPException
from sqlalchemy.orm import aliased, joinedload, raiseload

from app.db.auth import (
    constrain_entity_query_to_project,
    constrain_to_accessible_entities,
)
from app.db.model import (
    Agent,
    Publication,
    ScientificArtifact,
    ScientificArtifactPublicationLink,
)
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.scientific_artifact_publication_link import (
    ScientificArtifactPublicationLinkFilterDep,
)
from app.logger import L
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.queries.factory import query_params_factory
from app.schemas.scientific_artifact_publication_link import (
    ScientificArtifactPublicationLinkCreate,
    ScientificArtifactPublicationLinkRead,
)
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(query: sa.Select):
    return query.options(
        joinedload(ScientificArtifactPublicationLink.scientific_artifact),
        joinedload(ScientificArtifactPublicationLink.publication),
        joinedload(ScientificArtifactPublicationLink.created_by),
        joinedload(ScientificArtifactPublicationLink.updated_by),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> ScientificArtifactPublicationLinkRead:
    entity = router_read_one(
        db=db,
        id_=id_,
        db_model_class=ScientificArtifactPublicationLink,
        authorized_project_id=None,
        response_schema_class=ScientificArtifactPublicationLinkRead,
        apply_operations=_load,
    )
    if not (
        entity.scientific_artifact.authorized_public
        or entity.scientific_artifact.authorized_project_id == user_context.project_id
    ):
        L.warning("Attempting to fetch a link with scientific artifact inaccessible to user")
        raise HTTPException(
            status_code=404, detail=f"Cannot access scientific_artifact in link {id_}"
        )
    if not (
        entity.publication.authorized_public
        or entity.publication.authorized_project_id == user_context.project_id
    ):
        L.warning("Attempting to fetch a link with a publication inaccessible to user")
        raise HTTPException(status_code=404, detail=f"Cannot access publication in link {id_}")

    return entity


def create_one(
    db: SessionDep,
    json_model: ScientificArtifactPublicationLinkCreate,
    user_context: UserContextWithProjectIdDep,
) -> ScientificArtifactPublicationLinkRead:
    stmt = constrain_entity_query_to_project(
        sa.select(sa.func.count(Publication.id)).where(Publication.id == json_model.publication_id),
        user_context.project_id,
    )
    if db.execute(stmt).scalar_one() == 0:
        L.warning("Attempting to create a link for a pulbication inaccessible to user")
        raise HTTPException(
            status_code=404, detail=f"Cannot access publication {json_model.publication_id}"
        )
    stmt = constrain_entity_query_to_project(
        sa.select(sa.func.count(ScientificArtifact.id)).where(
            ScientificArtifact.id == json_model.scientific_artifact_id
        ),
        user_context.project_id,
    )
    if db.execute(stmt).scalar_one() == 0:
        L.warning("Attempting to create a link for a scientific artifact inaccessible to user")
        raise HTTPException(
            status_code=404,
            detail=f"Cannot access scientific artifact {json_model.scientific_artifact_id}",
        )
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=ScientificArtifactPublicationLink,
        response_schema_class=ScientificArtifactPublicationLinkRead,
        apply_operations=_load,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: ScientificArtifactPublicationLinkFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[ScientificArtifactPublicationLinkRead]:
    created_by_alias = aliased(Agent, flat=True)
    updated_by_alias = aliased(Agent, flat=True)
    scientific_artifact_alias = aliased(ScientificArtifact, flat=True, name="artifact")
    publication_alias = aliased(Publication, flat=True, name="publication")
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
        "scientific_artifact",
        "publication",
    ]

    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=ScientificArtifactPublicationLink,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )

    filter_query = lambda q: _load(
        constrain_to_accessible_entities(
            constrain_to_accessible_entities(
                q.join(
                    scientific_artifact_alias,
                    ScientificArtifactPublicationLink.scientific_artifact_id
                    == scientific_artifact_alias.id,
                ).join(
                    publication_alias,
                    ScientificArtifactPublicationLink.publication_id == publication_alias.id,
                ),
                user_context.project_id,
                db_model_class=scientific_artifact_alias,
            ),
            user_context.project_id,
            db_model_class=publication_alias,
        )
    )

    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=ScientificArtifactPublicationLink,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=filter_query,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=ScientificArtifactPublicationLinkRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
    )
