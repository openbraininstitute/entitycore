import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, contains_eager, joinedload, raiseload

from app.db.auth import (
    constrain_to_accessible_entities,
)
from app.db.model import (
    Agent,
    ExternalUrl,
    ScientificArtifact,
    ScientificArtifactExternalUrlLink,
)
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.scientific_artifact_external_url_link import (
    ScientificArtifactExternalUrlLinkFilterDep,
)
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.queries.entity import get_writable_entity
from app.queries.factory import query_params_factory
from app.schemas.scientific_artifact_external_url_link import (
    ScientificArtifactExternalUrlLinkCreate,
    ScientificArtifactExternalUrlLinkRead,
)
from app.schemas.types import ListResponse
from app.utils.entity import ensure_readable

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(query: sa.Select) -> sa.Select:
    return query.options(
        joinedload(ScientificArtifactExternalUrlLink.scientific_artifact, innerjoin=True),
        joinedload(ScientificArtifactExternalUrlLink.external_url, innerjoin=True),
        joinedload(ScientificArtifactExternalUrlLink.created_by, innerjoin=True),
        joinedload(ScientificArtifactExternalUrlLink.updated_by, innerjoin=True),
        raiseload("*"),
    )


def _load_with_eager(query: sa.Select, aliases):
    return query.options(
        contains_eager(
            ScientificArtifactExternalUrlLink.scientific_artifact.of_type(
                aliases[ScientificArtifact]
            )
        ),
        contains_eager(
            ScientificArtifactExternalUrlLink.external_url.of_type(aliases[ExternalUrl])
        ),
        contains_eager(
            ScientificArtifactExternalUrlLink.created_by.of_type(aliases[Agent]["created_by"])
        ),
        contains_eager(
            ScientificArtifactExternalUrlLink.updated_by.of_type(aliases[Agent]["updated_by"])
        ),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> ScientificArtifactExternalUrlLinkRead:
    entity = router_read_one(
        db=db,
        id_=id_,
        db_model_class=ScientificArtifactExternalUrlLink,
        user_context=None,
        response_schema_class=ScientificArtifactExternalUrlLinkRead,
        apply_operations=_load,
    )
    ensure_readable(entity.scientific_artifact, user_context.project_id)
    return entity


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> ScientificArtifactExternalUrlLinkRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=ScientificArtifactExternalUrlLink,
        user_context=None,
        response_schema_class=ScientificArtifactExternalUrlLinkRead,
        apply_operations=_load,
    )


def create_one(
    db: SessionDep,
    json_model: ScientificArtifactExternalUrlLinkCreate,
    user_context: UserContextWithProjectIdDep,
) -> ScientificArtifactExternalUrlLinkRead:
    # ensure linked entities are accessible to user's project id
    get_writable_entity(
        db, ScientificArtifact, json_model.scientific_artifact_id, user_context.project_id
    )
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=ScientificArtifactExternalUrlLink,
        response_schema_class=ScientificArtifactExternalUrlLinkRead,
        apply_operations=_load,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: ScientificArtifactExternalUrlLinkFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[ScientificArtifactExternalUrlLinkRead]:
    created_by_alias = aliased(Agent, flat=True)
    updated_by_alias = aliased(Agent, flat=True)
    scientific_artifact_alias = aliased(ScientificArtifact, flat=True, name="artifact")
    external_url_alias = aliased(ExternalUrl, flat=True, name="external_url")
    aliases: Aliases = {
        Agent: {
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
        },
        ScientificArtifact: scientific_artifact_alias,
        ExternalUrl: external_url_alias,
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
        db_model_class=ScientificArtifactExternalUrlLink,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )

    filter_query = lambda q: constrain_to_accessible_entities(
        q.join(
            scientific_artifact_alias,
            ScientificArtifactExternalUrlLink.scientific_artifact_id
            == scientific_artifact_alias.id,
        )
        .join(
            external_url_alias,
            ScientificArtifactExternalUrlLink.external_url_id == external_url_alias.id,
        )
        .join(
            created_by_alias,
            ScientificArtifactExternalUrlLink.created_by_id == created_by_alias.id,
        )
        .join(
            updated_by_alias,
            ScientificArtifactExternalUrlLink.updated_by_id == updated_by_alias.id,
        ),
        project_id=user_context.project_id,
        db_model_class=scientific_artifact_alias,
    )

    load_with_aliases = lambda q: _load_with_eager(q, aliases)

    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=ScientificArtifactExternalUrlLink,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=filter_query,
        apply_data_query_operations=load_with_aliases,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=ScientificArtifactExternalUrlLinkRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
    )
