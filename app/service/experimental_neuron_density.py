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
    ETypeClass,
    ETypeClassification,
    ExperimentalNeuronDensity,
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
from app.filters.density import ExperimentalNeuronDensityFilterDep
from app.queries import facets as fc
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.schemas.density import ExperimentalNeuronDensityCreate, ExperimentalNeuronDensityRead
from app.schemas.types import ListResponse


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: ExperimentalNeuronDensityFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[ExperimentalNeuronDensityRead]:
    subject_alias = aliased(Subject, flat=True)
    name_to_facet_query_params: dict[str, FacetQueryParams] = (
        fc.brain_region | fc.contribution | fc.etype | fc.mtype
    )
    name_to_facet_query_params |= {
        "subject.species": {"id": Species.id, "label": Species.name},
        "subject.strain": {"id": Strain.id, "label": Strain.name},
    }
    filter_joins = {
        "brain_region": lambda q: q.join(
            BrainRegion, ExperimentalNeuronDensity.brain_region_id == BrainRegion.id
        ),
        "subject": lambda q: q.outerjoin(
            subject_alias, ExperimentalNeuronDensity.subject_id == subject_alias.id
        ),
        "subject.species": lambda q: q.outerjoin(Species, subject_alias.species_id == Species.id),
        "subject.strain": lambda q: q.outerjoin(Strain, subject_alias.strain_id == Strain.id),
        "contribution": lambda q: q.outerjoin(
            Contribution, ExperimentalNeuronDensity.id == Contribution.entity_id
        ).outerjoin(Agent, Contribution.agent_id == Agent.id),
        "mtype": lambda q: q.outerjoin(
            MTypeClassification, ExperimentalNeuronDensity.id == MTypeClassification.entity_id
        ).outerjoin(MTypeClass, MTypeClass.id == MTypeClassification.mtype_class_id),
        "etype": lambda q: q.outerjoin(
            ETypeClassification, ExperimentalNeuronDensity.id == ETypeClassification.entity_id
        ).outerjoin(ETypeClass, ETypeClass.id == ETypeClassification.etype_class_id),
    }
    apply_data_options = lambda query: (
        query.options(joinedload(ExperimentalNeuronDensity.brain_region))
        .options(
            selectinload(ExperimentalNeuronDensity.contributions).selectinload(Contribution.agent)
        )
        .options(
            selectinload(ExperimentalNeuronDensity.contributions).selectinload(Contribution.role)
        )
        .options(joinedload(ExperimentalNeuronDensity.mtypes))
        .options(joinedload(ExperimentalNeuronDensity.etypes))
        .options(joinedload(ExperimentalNeuronDensity.license))
        .options(joinedload(ExperimentalNeuronDensity.subject).joinedload(Subject.species))
        .options(joinedload(ExperimentalNeuronDensity.subject).joinedload(Subject.strain))
        .options(selectinload(ExperimentalNeuronDensity.assets))
        .options(selectinload(ExperimentalNeuronDensity.measurements))
        .options(raiseload("*"))
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=ExperimentalNeuronDensity,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=apply_data_options,
        aliases={Subject: subject_alias},
        pagination_request=pagination_request,
        response_schema_class=ExperimentalNeuronDensityRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> ExperimentalNeuronDensityRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=ExperimentalNeuronDensity,
        authorized_project_id=user_context.project_id,
        response_schema_class=ExperimentalNeuronDensityRead,
        apply_operations=lambda q: q.options(
            joinedload(ExperimentalNeuronDensity.brain_region),
            joinedload(ExperimentalNeuronDensity.mtypes),
            joinedload(ExperimentalNeuronDensity.etypes),
            joinedload(ExperimentalNeuronDensity.assets),
            joinedload(ExperimentalNeuronDensity.license),
            joinedload(ExperimentalNeuronDensity.subject).joinedload(Subject.strain),
            joinedload(ExperimentalNeuronDensity.subject).joinedload(Subject.species),
            selectinload(ExperimentalNeuronDensity.measurements),
            selectinload(ExperimentalNeuronDensity.contributions).selectinload(Contribution.agent),
            selectinload(ExperimentalNeuronDensity.contributions).selectinload(Contribution.role),
            raiseload("*"),
        ),
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    json_model: ExperimentalNeuronDensityCreate,
    db: SessionDep,
) -> ExperimentalNeuronDensityRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        db_model_class=ExperimentalNeuronDensity,
        authorized_project_id=user_context.project_id,
        response_schema_class=ExperimentalNeuronDensityRead,
    )
