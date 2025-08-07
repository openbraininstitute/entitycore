import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, contains_eager, joinedload, raiseload

from app.db.auth import (
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
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.queries.entity import get_writable_entity
from app.queries.factory import query_params_factory
from app.schemas.scientific_artifact_publication_link import (
    ScientificArtifactPublicationLinkCreate,
    ScientificArtifactPublicationLinkRead,
)
from app.schemas.types import ListResponse
from app.utils.entity import ensure_readable

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(query: sa.Select):
    return query.options(
        joinedload(ScientificArtifactPublicationLink.scientific_artifact, innerjoin=True),
        joinedload(ScientificArtifactPublicationLink.publication, innerjoin=True),
        joinedload(ScientificArtifactPublicationLink.created_by, innerjoin=True),
        joinedload(ScientificArtifactPublicationLink.updated_by, innerjoin=True),
        raiseload("*"),
    )


def _load_with_eager(query: sa.Select, aliases):
    return query.options(
        contains_eager(
            ScientificArtifactPublicationLink.scientific_artifact.of_type(
                aliases[ScientificArtifact]
            )
        ),
        contains_eager(ScientificArtifactPublicationLink.publication.of_type(aliases[Publication])),
        contains_eager(
            ScientificArtifactPublicationLink.created_by.of_type(aliases[Agent]["created_by"])
        ),
        contains_eager(
            ScientificArtifactPublicationLink.updated_by.of_type(aliases[Agent]["updated_by"])
        ),
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
    ensure_readable(entity.scientific_artifact, user_context.project_id)
    return entity


def create_one(
    db: SessionDep,
    json_model: ScientificArtifactPublicationLinkCreate,
    user_context: UserContextWithProjectIdDep,
) -> ScientificArtifactPublicationLinkRead:
    # ensure linked entities are accessible to user's project id
    get_writable_entity(
        db, ScientificArtifact, json_model.scientific_artifact_id, user_context.project_id
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
        ScientificArtifact: scientific_artifact_alias,
        Publication: publication_alias,
    }
    facet_keys = [
        "created_by",
        "updated_by",
    ]
    filter_keys = [
        "created_by",
        "updated_by",
    ]

    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=ScientificArtifactPublicationLink,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )

    filter_query = lambda q: constrain_to_accessible_entities(
        q.join(
            scientific_artifact_alias,
            ScientificArtifactPublicationLink.scientific_artifact_id
            == scientific_artifact_alias.id,
        )
        .join(
            publication_alias,
            ScientificArtifactPublicationLink.publication_id == publication_alias.id,
        )
        .join(
            created_by_alias,
            ScientificArtifactPublicationLink.created_by_id == created_by_alias.id,
        )
        .join(
            updated_by_alias,
            ScientificArtifactPublicationLink.updated_by_id == updated_by_alias.id,
        ),
        project_id=user_context.project_id,
        db_model_class=scientific_artifact_alias,
    )

    load_with_aliases = lambda q: _load_with_eager(q, aliases)

    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=ScientificArtifactPublicationLink,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=filter_query,
        apply_data_query_operations=load_with_aliases,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=ScientificArtifactPublicationLinkRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
    )
