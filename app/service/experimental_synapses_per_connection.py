import uuid

import sqlalchemy as sa
from sqlalchemy.orm import (
    aliased,
    joinedload,
    raiseload,
    selectinload,
)

from app.db.model import (
    Agent,
    BrainRegion,
    Contribution,
    ExperimentalSynapsesPerConnection,
    MTypeClass,
    Subject,
)
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.density import ExperimentalSynapsesPerConnectionFilterDep
from app.queries.common import (
    router_create_one,
    router_delete_one,
    router_read_many,
    router_read_one,
    router_update_one,
)
from app.queries.factory import query_params_factory
from app.schemas.density import (
    ExperimentalSynapsesPerConnectionAdminUpdate,
    ExperimentalSynapsesPerConnectionCreate,
    ExperimentalSynapsesPerConnectionRead,
    ExperimentalSynapsesPerConnectionUserUpdate,
)
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse


def _load(q: sa.Select):
    db_cls = ExperimentalSynapsesPerConnection
    return q.options(
        joinedload(db_cls.brain_region),
        selectinload(db_cls.contributions).selectinload(Contribution.agent),
        selectinload(db_cls.contributions).selectinload(Contribution.role),
        joinedload(db_cls.license),
        joinedload(db_cls.subject).joinedload(Subject.species),
        joinedload(db_cls.subject).joinedload(Subject.strain),
        joinedload(db_cls.created_by),
        joinedload(db_cls.updated_by),
        joinedload(db_cls.pre_mtype),
        joinedload(db_cls.post_mtype),
        joinedload(db_cls.pre_region),
        joinedload(db_cls.post_region),
        selectinload(db_cls.assets),
        selectinload(db_cls.measurements),
        raiseload("*"),
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: ExperimentalSynapsesPerConnectionFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[ExperimentalSynapsesPerConnectionRead]:
    subject_alias = aliased(Subject, flat=True)
    pre_mtype_alias = aliased(MTypeClass, flat=True)
    post_mtype_alias = aliased(MTypeClass, flat=True)
    brain_region_alias = aliased(BrainRegion, flat=True)
    pre_region_alias = aliased(BrainRegion, flat=True)
    post_region_alias = aliased(BrainRegion, flat=True)
    agent_alias = aliased(Agent, flat=True)
    created_by_alias = aliased(Agent, flat=True)
    updated_by_alias = aliased(Agent, flat=True)
    aliases = {
        Subject: subject_alias,
        BrainRegion: {
            "brain_region": brain_region_alias,
            "pre_region": pre_region_alias,
            "post_region": post_region_alias,
        },
        MTypeClass: {
            "pre_mtype": pre_mtype_alias,
            "post_mtype": post_mtype_alias,
        },
        Agent: {
            "contribution": agent_alias,
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
        },
    }
    facet_keys = [
        "pre_mtype",
        "post_mtype",
        "pre_region",
        "post_region",
        "brain_region",
        "created_by",
        "updated_by",
        "contribution",
        "subject.species",
        "subject.strain",
    ]
    filter_keys = [
        "pre_mtype",
        "post_mtype",
        "pre_region",
        "post_region",
        "brain_region",
        "created_by",
        "updated_by",
        "contribution",
        "subject",
        "subject.species",
        "subject.strain",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=ExperimentalSynapsesPerConnection,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=ExperimentalSynapsesPerConnection,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        aliases=aliases,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        pagination_request=pagination_request,
        response_schema_class=ExperimentalSynapsesPerConnectionRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> ExperimentalSynapsesPerConnectionRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=ExperimentalSynapsesPerConnection,
        authorized_project_id=user_context.project_id,
        response_schema_class=ExperimentalSynapsesPerConnectionRead,
        apply_operations=_load,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> ExperimentalSynapsesPerConnectionRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=ExperimentalSynapsesPerConnection,
        authorized_project_id=None,
        response_schema_class=ExperimentalSynapsesPerConnectionRead,
        apply_operations=_load,
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    json_model: ExperimentalSynapsesPerConnectionCreate,
    db: SessionDep,
) -> ExperimentalSynapsesPerConnectionRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=ExperimentalSynapsesPerConnection,
        response_schema_class=ExperimentalSynapsesPerConnectionRead,
        apply_operations=_load,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: ExperimentalSynapsesPerConnectionUserUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> ExperimentalSynapsesPerConnectionRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=ExperimentalSynapsesPerConnection,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=ExperimentalSynapsesPerConnectionRead,
        apply_operations=_load,
    )


def admin_update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: ExperimentalSynapsesPerConnectionAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> ExperimentalSynapsesPerConnectionRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=ExperimentalSynapsesPerConnection,
        user_context=None,
        json_model=json_model,
        response_schema_class=ExperimentalSynapsesPerConnectionRead,
        apply_operations=_load,
    )


def delete_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> DeleteResponse:
    return router_delete_one(
        id_=id_,
        db=db,
        db_model_class=ExperimentalSynapsesPerConnection,
        user_context=user_context,
    )
