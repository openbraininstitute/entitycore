import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload

from app.db.auth import (
    constrain_to_readable_entities,
)
from app.db.model import (
    ExternalUrl,
    Person,
    ScientificArtifact,
    ScientificArtifactExternalUrlLink,
)
from app.dependencies.auth import AdminContextDep, UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
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
from app.routers.types import AssociationRoute
from app.schemas.routers import DeleteResponse
from app.schemas.scientific_artifact_external_url_link import (
    ScientificArtifactExternalUrlLinkCreate,
    ScientificArtifactExternalUrlLinkRead,
)
from app.schemas.types import ListResponse
from app.service import admin as admin_service
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


def _read_many(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: ScientificArtifactExternalUrlLinkFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    check_authorized_project: bool,
) -> ListResponse[ScientificArtifactExternalUrlLinkRead]:
    created_by_alias = aliased(Person, flat=True)
    updated_by_alias = aliased(Person, flat=True)
    scientific_artifact_alias = aliased(ScientificArtifact, flat=True, name="artifact")
    external_url_alias = aliased(ExternalUrl, flat=True, name="external_url")
    aliases: Aliases = {
        Person: {
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
    base_join_query = lambda q: q.join(
        scientific_artifact_alias,
        ScientificArtifactExternalUrlLink.scientific_artifact_id == scientific_artifact_alias.id,
    ).join(
        external_url_alias,
        ScientificArtifactExternalUrlLink.external_url_id == external_url_alias.id,
    )

    if check_authorized_project:
        filter_query = lambda q: constrain_to_readable_entities(
            base_join_query(q),
            project_id=user_context.project_id,
            db_model_class=scientific_artifact_alias,
        )
    else:
        filter_query = base_join_query

    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=ScientificArtifactExternalUrlLink,
        with_search=with_search,
        with_in_brain_region=None,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=filter_query,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=ScientificArtifactExternalUrlLinkRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
        check_authorized_project=check_authorized_project,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    with_search: SearchDep,
    facets: FacetsDep,
    pagination_request: PaginationQuery,
    filter_model: ScientificArtifactExternalUrlLinkFilterDep,
) -> ListResponse[ScientificArtifactExternalUrlLinkRead]:
    return _read_many(
        user_context=user_context,
        db=db,
        with_search=with_search,
        facets=facets,
        pagination_request=pagination_request,
        filter_model=filter_model,
        check_authorized_project=True,
    )


def admin_read_many(
    user_context: AdminContextDep,
    db: SessionDep,
    with_search: SearchDep,
    facets: FacetsDep,
    pagination_request: PaginationQuery,
    filter_model: ScientificArtifactExternalUrlLinkFilterDep,
) -> ListResponse[ScientificArtifactExternalUrlLinkRead]:
    return _read_many(
        user_context=user_context,
        db=db,
        with_search=with_search,
        facets=facets,
        pagination_request=pagination_request,
        filter_model=filter_model,
        check_authorized_project=False,
    )


def admin_delete_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> DeleteResponse:
    return admin_service.delete_one(
        db=db,
        route=AssociationRoute.scientific_artifact_external_url_link,
        id_=id_,
    )
