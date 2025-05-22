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
    Species,
    Strain,
    Subject,
)
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetQueryParams,
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.density import ExperimentalSynapsesPerConnectionFilterDep
from app.queries import facets as fc
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.schemas.density import (
    ExperimentalSynapsesPerConnectionCreate,
    ExperimentalSynapsesPerConnectionRead,
)
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
    pre_region_alias = aliased(BrainRegion, flat=True)
    post_region_alias = aliased(BrainRegion, flat=True)
    agent_alias = aliased(Agent, flat=True)
    created_by_alias = aliased(Agent, flat=True)
    updated_by_alias = aliased(Agent, flat=True)
    aliases = {
        Subject: subject_alias,
        BrainRegion: {
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
    aliased_facets: dict[str, FacetQueryParams] = {
        "pre_mtype": {
            "id": pre_mtype_alias.id,
            "label": pre_mtype_alias.pref_label,
        },
        "post_mtype": {
            "id": post_mtype_alias.id,
            "label": post_mtype_alias.pref_label,
        },
        "pre_region": {
            "id": pre_region_alias.id,
            "label": pre_region_alias.name,
        },
        "post_region": {
            "id": post_region_alias.id,
            "label": post_region_alias.name,
        },
        "contribution": {
            "id": agent_alias.id,
            "label": agent_alias.pref_label,
            "type": agent_alias.type,
        },
        "created_by": {
            "id": created_by_alias.id,
            "label": created_by_alias.pref_label,
            "type": created_by_alias.type,
        },
        "updated_by": {
            "id": updated_by_alias.id,
            "label": updated_by_alias.pref_label,
            "type": updated_by_alias.type,
        },
    }

    name_to_facet_query_params: dict[str, FacetQueryParams] = (
        fc.brain_region | fc.subject | aliased_facets
    )

    db_cls = ExperimentalSynapsesPerConnection

    filter_joins = {
        "brain_region": lambda q: q.join(BrainRegion, db_cls.brain_region_id == BrainRegion.id),
        "pre_mtype": lambda q: q.join(pre_mtype_alias, db_cls.pre_mtype_id == pre_mtype_alias.id),
        "post_mtype": lambda q: q.join(
            post_mtype_alias, db_cls.post_mtype_id == post_mtype_alias.id
        ),
        "pre_region": lambda q: q.join(
            pre_region_alias, db_cls.pre_region_id == pre_region_alias.id
        ),
        "post_region": lambda q: q.join(
            post_region_alias, db_cls.post_region_id == post_region_alias.id
        ),
        "subject": lambda q: q.outerjoin(subject_alias, db_cls.subject_id == subject_alias.id),
        "subject.species": lambda q: q.outerjoin(Species, subject_alias.species_id == Species.id),
        "subject.strain": lambda q: q.outerjoin(Strain, subject_alias.strain_id == Strain.id),
        "contribution": lambda q: q.outerjoin(
            Contribution, db_cls.id == Contribution.entity_id
        ).outerjoin(agent_alias, Contribution.agent_id == agent_alias.id),
        "created_by": lambda q: q.outerjoin(
            created_by_alias, db_cls.created_by_id == created_by_alias.id
        ),
        "updated_by": lambda q: q.outerjoin(
            updated_by_alias, db_cls.updated_by_id == updated_by_alias.id
        ),
    }
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
    )
