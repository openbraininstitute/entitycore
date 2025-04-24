import uuid

from sqlalchemy.orm import joinedload, raiseload

from app.db.model import Agent, Contribution, Subject
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import FacetQueryParams, FacetsDep, PaginationQuery, SearchDep
from app.dependencies.db import SessionDep
from app.filters.common import SubjectFilterDep
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.schemas.base import SubjectCreate, SubjectRead
from app.schemas.types import ListResponse


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> SubjectRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=Subject,
        authorized_project_id=user_context.project_id,
        response_schema_class=SubjectRead,
        apply_operations=lambda q: q.options(
            joinedload(Subject.species),
        ),
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    json_model: SubjectCreate,
) -> SubjectRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        db_model_class=Subject,
        authorized_project_id=user_context.project_id,
        response_schema_class=SubjectRead,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: SubjectFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
) -> ListResponse[SubjectRead]:
    name_to_facet_query_params: dict[str, FacetQueryParams] = {
        "contribution": {
            "id": Agent.id,
            "label": Agent.pref_label,
            "type": Agent.type,
        },
    }
    apply_filter_query = lambda query: (
        query.outerjoin(Contribution, Subject.id == Contribution.entity_id).outerjoin(
            Agent, Contribution.agent_id == Agent.id
        )
    )
    apply_data_options = lambda query: (
        query.options(joinedload(Subject.species)).options(raiseload("*"))
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=Subject,
        with_search=with_search,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=apply_filter_query,
        apply_data_query_operations=apply_data_options,
        aliases={},
        pagination_request=pagination_request,
        response_schema_class=SubjectRead,
        authorized_project_id=user_context.project_id,
    )
