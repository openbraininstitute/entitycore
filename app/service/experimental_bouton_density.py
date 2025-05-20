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
    ExperimentalBoutonDensity,
    MTypeClass,
    MTypeClassification,
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
from app.filters.density import ExperimentalBoutonDensityFilterDep
from app.queries import facets as fc
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.schemas.density import ExperimentalBoutonDensityCreate, ExperimentalBoutonDensityRead
from app.schemas.types import ListResponse


def _load(query: sa.Select):
    return query.options(
        joinedload(ExperimentalBoutonDensity.brain_region),
        joinedload(ExperimentalBoutonDensity.mtypes),
        joinedload(ExperimentalBoutonDensity.subject).joinedload(Subject.species),
        joinedload(ExperimentalBoutonDensity.subject).joinedload(Subject.strain),
        joinedload(ExperimentalBoutonDensity.assets),
        joinedload(ExperimentalBoutonDensity.license),
        joinedload(ExperimentalBoutonDensity.createdBy),
        joinedload(ExperimentalBoutonDensity.updatedBy),
        selectinload(ExperimentalBoutonDensity.measurements),
        selectinload(ExperimentalBoutonDensity.contributions).selectinload(Contribution.agent),
        selectinload(ExperimentalBoutonDensity.contributions).selectinload(Contribution.role),
        raiseload("*"),
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: ExperimentalBoutonDensityFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[ExperimentalBoutonDensityRead]:
    subject = aliased(Subject, flat=True)
    agent_alias = aliased(Agent, flat=True)
    created_by_alias = aliased(Agent, flat=True)
    updated_by_alias = aliased(Agent, flat=True)
    aliases = {
        Subject: subject,
        Agent: {
            "contribution": agent_alias,
            "createdBy": created_by_alias,
            "updatedBy": updated_by_alias,
        },
    }
    aliased_facets: dict[str, FacetQueryParams] = {
        "contribution": {
            "id": agent_alias.id,
            "label": agent_alias.pref_label,
            "type": agent_alias.type,
        },
        "createdBy": {
            "id": created_by_alias.id,
            "label": created_by_alias.pref_label,
            "type": created_by_alias.type,
        },
        "updatedBy": {
            "id": updated_by_alias.id,
            "label": updated_by_alias.pref_label,
            "type": updated_by_alias.type,
        },
    }
    name_to_facet_query_params: dict[str, FacetQueryParams] = (
        fc.brain_region | fc.mtype | fc.subject | aliased_facets
    )
    filter_joins = {
        "brain_region": lambda q: q.join(
            BrainRegion, ExperimentalBoutonDensity.brain_region_id == BrainRegion.id
        ),
        "subject": lambda q: q.outerjoin(
            subject, ExperimentalBoutonDensity.subject_id == subject.id
        ),
        "subject.species": lambda q: q.outerjoin(Species, subject.species_id == Species.id),
        "subject.strain": lambda q: q.outerjoin(Strain, subject.strain_id == Strain.id),
        "contribution": lambda q: q.outerjoin(
            Contribution, ExperimentalBoutonDensity.id == Contribution.entity_id
        ).outerjoin(agent_alias, Contribution.agent_id == agent_alias.id),
        "createdBy": lambda q: q.outerjoin(
            created_by_alias, ExperimentalBoutonDensity.createdBy_id == created_by_alias.id
        ),
        "updatedBy": lambda q: q.outerjoin(
            updated_by_alias, ExperimentalBoutonDensity.updatedBy_id == updated_by_alias.id
        ),
        "mtype": lambda q: q.outerjoin(
            MTypeClassification, ExperimentalBoutonDensity.id == MTypeClassification.entity_id
        ).outerjoin(MTypeClass, MTypeClass.id == MTypeClassification.mtype_class_id),
    }
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=ExperimentalBoutonDensity,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=ExperimentalBoutonDensityRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> ExperimentalBoutonDensityRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=ExperimentalBoutonDensity,
        authorized_project_id=user_context.project_id,
        response_schema_class=ExperimentalBoutonDensityRead,
        apply_operations=_load,
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    json_model: ExperimentalBoutonDensityCreate,
    db: SessionDep,
) -> ExperimentalBoutonDensityRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=ExperimentalBoutonDensity,
        response_schema_class=ExperimentalBoutonDensityRead,
    )
