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
    ExperimentalBoutonDensity,
    MTypeClass,
    MTypeClassification,
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
    name_to_facet_query_params: dict[str, FacetQueryParams] = (
        fc.brain_region | fc.contribution | fc.mtype | fc.species | fc.strain
    )
    apply_filter_query = lambda query: (
        query.join(BrainRegion, ExperimentalBoutonDensity.brain_region_id == BrainRegion.id)
        .outerjoin(subject, ExperimentalBoutonDensity.subject_id == subject.id)
        .outerjoin(Contribution, ExperimentalBoutonDensity.id == Contribution.entity_id)
        .outerjoin(Agent, Contribution.agent_id == Agent.id)
        .outerjoin(
            MTypeClassification, ExperimentalBoutonDensity.id == MTypeClassification.entity_id
        )
        .outerjoin(MTypeClass, MTypeClass.id == MTypeClassification.mtype_class_id)
    )
    apply_data_options = lambda query: (
        query.options(joinedload(ExperimentalBoutonDensity.brain_region))
        .options(
            selectinload(ExperimentalBoutonDensity.contributions).selectinload(Contribution.agent)
        )
        .options(
            selectinload(ExperimentalBoutonDensity.contributions).selectinload(Contribution.role)
        )
        .options(joinedload(ExperimentalBoutonDensity.mtypes))
        .options(joinedload(ExperimentalBoutonDensity.license))
        .options(joinedload(ExperimentalBoutonDensity.subject).joinedload(Subject.species))
        .options(joinedload(ExperimentalBoutonDensity.subject).joinedload(Subject.strain))
        .options(selectinload(ExperimentalBoutonDensity.assets))
        .options(selectinload(ExperimentalBoutonDensity.measurements))
        .options(raiseload("*"))
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=ExperimentalBoutonDensity,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=apply_filter_query,
        apply_data_query_operations=apply_data_options,
        aliases={Subject: subject},
        pagination_request=pagination_request,
        response_schema_class=ExperimentalBoutonDensityRead,
        authorized_project_id=user_context.project_id,
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
        apply_operations=lambda q: q.options(
            joinedload(ExperimentalBoutonDensity.brain_region),
            joinedload(ExperimentalBoutonDensity.mtypes),
            joinedload(ExperimentalBoutonDensity.subject).joinedload(Subject.species),
            joinedload(ExperimentalBoutonDensity.subject).joinedload(Subject.strain),
            joinedload(ExperimentalBoutonDensity.assets),
            joinedload(ExperimentalBoutonDensity.license),
            selectinload(ExperimentalBoutonDensity.measurements),
            selectinload(ExperimentalBoutonDensity.contributions).selectinload(Contribution.agent),
            selectinload(ExperimentalBoutonDensity.contributions).selectinload(Contribution.role),
            raiseload("*"),
        ),
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    json_model: ExperimentalBoutonDensityCreate,
    db: SessionDep,
) -> ExperimentalBoutonDensityRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        db_model_class=ExperimentalBoutonDensity,
        authorized_project_id=user_context.project_id,
        response_schema_class=ExperimentalBoutonDensityRead,
    )
