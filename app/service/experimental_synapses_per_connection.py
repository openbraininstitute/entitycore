import uuid

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
    Subject,
    SynapticPathway,
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


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: ExperimentalSynapsesPerConnectionFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[ExperimentalSynapsesPerConnectionRead]:
    pathway_alias = aliased(SynapticPathway, flat=True)
    subject_alias = aliased(Subject, flat=True)
    name_to_facet_query_params: dict[str, FacetQueryParams] = (
        fc.brain_region | fc.contribution | fc.mtype | fc.species | fc.strain | fc.synaptic_pathway
    )

    apply_filter_query = lambda query: (
        query.join(BrainRegion, ExperimentalSynapsesPerConnection.brain_region_id == BrainRegion.id)
        .outerjoin(subject_alias, ExperimentalSynapsesPerConnection.subject_id == subject_alias.id)
        .outerjoin(
            pathway_alias,
            ExperimentalSynapsesPerConnection.synaptic_pathway_id == pathway_alias.id,
        )
        .outerjoin(Contribution, ExperimentalSynapsesPerConnection.id == Contribution.entity_id)
        .outerjoin(Agent, Contribution.agent_id == Agent.id)
    )
    apply_data_options = lambda query: (
        query.options(joinedload(ExperimentalSynapsesPerConnection.brain_region))
        .options(
            selectinload(ExperimentalSynapsesPerConnection.contributions).selectinload(
                Contribution.agent
            )
        )
        .options(
            selectinload(ExperimentalSynapsesPerConnection.contributions).selectinload(
                Contribution.role
            )
        )
        .options(joinedload(ExperimentalSynapsesPerConnection.license))
        .options(joinedload(ExperimentalSynapsesPerConnection.subject).joinedload(Subject.species))
        .options(joinedload(ExperimentalSynapsesPerConnection.subject).joinedload(Subject.strain))
        .options(
            joinedload(ExperimentalSynapsesPerConnection.synaptic_pathway).joinedload(
                SynapticPathway.pre_mtype
            )
        )
        .options(
            joinedload(ExperimentalSynapsesPerConnection.synaptic_pathway).joinedload(
                SynapticPathway.post_mtype
            )
        )
        .options(
            joinedload(ExperimentalSynapsesPerConnection.synaptic_pathway).joinedload(
                SynapticPathway.pre_region
            )
        )
        .options(
            joinedload(ExperimentalSynapsesPerConnection.synaptic_pathway).joinedload(
                SynapticPathway.post_region
            )
        )
        .options(selectinload(ExperimentalSynapsesPerConnection.assets))
        .options(selectinload(ExperimentalSynapsesPerConnection.measurements))
        .options(raiseload("*"))
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=ExperimentalSynapsesPerConnection,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        aliases={SynapticPathway: pathway_alias, Subject: subject_alias},
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=apply_filter_query,
        apply_data_query_operations=apply_data_options,
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
        apply_operations=lambda q: q.options(
            joinedload(ExperimentalSynapsesPerConnection.brain_region),
            joinedload(ExperimentalSynapsesPerConnection.assets),
            joinedload(ExperimentalSynapsesPerConnection.license),
            joinedload(ExperimentalSynapsesPerConnection.subject).joinedload(Subject.species),
            joinedload(ExperimentalSynapsesPerConnection.subject).joinedload(Subject.strain),
            joinedload(ExperimentalSynapsesPerConnection.synaptic_pathway).joinedload(
                SynapticPathway.pre_mtype
            ),
            joinedload(ExperimentalSynapsesPerConnection.synaptic_pathway).joinedload(
                SynapticPathway.post_mtype
            ),
            joinedload(ExperimentalSynapsesPerConnection.synaptic_pathway).joinedload(
                SynapticPathway.pre_region
            ),
            joinedload(ExperimentalSynapsesPerConnection.synaptic_pathway).joinedload(
                SynapticPathway.post_region
            ),
            selectinload(ExperimentalSynapsesPerConnection.measurements),
            selectinload(ExperimentalSynapsesPerConnection.contributions).selectinload(
                Contribution.agent
            ),
            selectinload(ExperimentalSynapsesPerConnection.contributions).selectinload(
                Contribution.role
            ),
            raiseload("*"),
        ),
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
