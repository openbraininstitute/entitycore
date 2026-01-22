import uuid
from typing import TYPE_CHECKING

from sqlalchemy.orm import aliased, joinedload, raiseload, selectinload

from app.db.model import Mapping, Person, Subject
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import FacetsDep, InBrainRegionDep, PaginationQuery, SearchDep
from app.dependencies.db import SessionDep
from app.filters.mapping import MappingFilterDep
from app.queries.common import (
    router_create_one,
    router_read_many,
    router_read_one,
    router_update_one,
    router_user_delete_one,
)
from app.queries.factory import query_params_factory
from app.schemas.mapping import (
    MappingAdminUpdate,
    MappingCreate,
    MappingRead,
    MappingUserUpdate,
)
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse, Select

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(q: Select[Mapping]) -> Select[Mapping]:
    db_model_class = Mapping
    return q.options(
        joinedload(db_model_class.subject, innerjoin=True).selectinload(Subject.species),
        joinedload(db_model_class.subject, innerjoin=True).selectinload(Subject.strain),
        joinedload(db_model_class.brain_region, innerjoin=True),
        joinedload(db_model_class.created_by),
        joinedload(db_model_class.updated_by),
        joinedload(db_model_class.license),
        selectinload(db_model_class.contributions),
        selectinload(db_model_class.assets),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> MappingRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=Mapping,
        user_context=user_context,
        response_schema_class=MappingRead,
        apply_operations=_load,
    )


def admin_update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: MappingAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> MappingRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=Mapping,
        user_context=None,
        json_model=json_model,
        response_schema_class=MappingRead,
        apply_operations=_load,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> MappingRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=Mapping,
        user_context=None,
        response_schema_class=MappingRead,
        apply_operations=_load,
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    json_model: MappingCreate,
) -> MappingRead:
    return router_create_one(
        db=db,
        apply_operations=_load,
        user_context=user_context,
        json_model=json_model,
        db_model_class=Mapping,
        response_schema_class=MappingRead,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: MappingUserUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> MappingRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=Mapping,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=MappingRead,
        apply_operations=_load,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: MappingFilterDep,
    with_search: SearchDep,
    in_brain_region: InBrainRegionDep,
    facets: FacetsDep,
) -> ListResponse[MappingRead]:
    subject_alias = aliased(Subject, flat=True)
    aliases: Aliases = {
        Subject: subject_alias,
        Person: {
            "created_by": aliased(Person, flat=True),
            "updated_by": aliased(Person, flat=True),
        },
    }
    facet_keys = [
        "created_by",
        "updated_by",
        "brain_region",
        "subject.species",
        "subject.strain",
    ]
    filter_keys = [
        "created_by",
        "updated_by",
        "brain_region",
        "subject",
        "subject.species",
        "subject.strain",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=Mapping,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        db_model_class=Mapping,
        authorized_project_id=user_context.project_id,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        aliases=aliases,
        apply_data_query_operations=_load,
        apply_filter_query_operations=None,
        pagination_request=pagination_request,
        response_schema_class=MappingRead,
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=filter_model,
        filter_joins=filter_joins,
    )


def delete_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> DeleteResponse:
    return router_user_delete_one(
        id_=id_,
        db=db,
        db_model_class=Mapping,
        user_context=user_context,
    )
