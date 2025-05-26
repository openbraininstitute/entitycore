import uuid

from sqlalchemy.orm import joinedload, raiseload

from app.db.model import Subject
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import FacetsDep, PaginationQuery, SearchDep
from app.dependencies.db import SessionDep
from app.filters.common import SubjectFilterDep
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.queries.factory import query_params_factory
from app.schemas.subject import SubjectCreate, SubjectRead
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
        user_context=user_context,
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
    facet_keys = filter_keys = [
        "contribution",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=Subject,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases={},
    )
    apply_data_options = lambda query: (
        query.options(joinedload(Subject.species)).options(raiseload("*"))
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=Subject,
        with_search=with_search,
        with_in_brain_region=None,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=apply_data_options,
        aliases={},
        pagination_request=pagination_request,
        response_schema_class=SubjectRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
    )
