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

    synaptic_pathway_facets: dict[str, FacetQueryParams] = {
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
    }

    name_to_facet_query_params: dict[str, FacetQueryParams] = (
        fc.brain_region | fc.contribution | fc.species | fc.strain | synaptic_pathway_facets
    )

    db_cls = ExperimentalSynapsesPerConnection

    apply_filter_query = lambda query: (
        query.join(BrainRegion, db_cls.brain_region_id == BrainRegion.id)
        .join(pre_mtype_alias, db_cls.pre_mtype_id == pre_mtype_alias.id)
        .join(post_mtype_alias, db_cls.post_mtype_id == post_mtype_alias.id)
        .join(pre_region_alias, db_cls.pre_region_id == pre_region_alias.id)
        .join(post_region_alias, db_cls.post_region_id == post_region_alias.id)
        .outerjoin(subject_alias, db_cls.subject_id == subject_alias.id)
        .outerjoin(Species, subject_alias.species_id == Species.id)
        .outerjoin(Strain, subject_alias.strain_id == Strain.id)
        .outerjoin(Contribution, db_cls.id == Contribution.entity_id)
        .outerjoin(Agent, Contribution.agent_id == Agent.id)
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=ExperimentalSynapsesPerConnection,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        aliases={
            Subject: subject_alias,
            BrainRegion: {
                "pre_region": pre_region_alias,
                "post_region": post_region_alias,
            },
            MTypeClass: {
                "pre_mtype": pre_mtype_alias,
                "post_mtype": post_mtype_alias,
            },
        },
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=apply_filter_query,
        apply_data_query_operations=_load,
        pagination_request=pagination_request,
        response_schema_class=ExperimentalSynapsesPerConnectionRead,
        authorized_project_id=user_context.project_id,
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
        db_model_class=ExperimentalSynapsesPerConnection,
        authorized_project_id=user_context.project_id,
        response_schema_class=ExperimentalSynapsesPerConnectionRead,
    )
