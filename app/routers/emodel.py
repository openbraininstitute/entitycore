import uuid

from fastapi import APIRouter
from sqlalchemy.orm import aliased, joinedload, raiseload, selectinload
from sqlalchemy.sql.selectable import Select

from app.db.model import (
    Agent,
    BrainRegion,
    Contribution,
    EModel,
    ETypeClass,
    ETypeClassification,
    MTypeClass,
    MTypeClassification,
    ReconstructionMorphology,
    Species,
)
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import FacetQueryParams, FacetsDep, PaginationQuery, SearchDep
from app.dependencies.db import SessionDep
from app.errors import (
    ensure_authorized_references,
)
from app.filters.emodel import EModelFilterDep
from app.routers.common import router_create_one, router_read_many, router_read_one
from app.schemas.emodel import EModelCreate, EModelRead
from app.schemas.types import ListResponse

router = APIRouter(
    prefix="/emodel",
    tags=["emodel"],
)


def load(select: Select):
    return select.options(
        joinedload(EModel.species),
        joinedload(EModel.strain),
        joinedload(EModel.exemplar_morphology),
        joinedload(EModel.brain_region),
        selectinload(EModel.contributions).joinedload(Contribution.agent),
        selectinload(EModel.contributions).joinedload(Contribution.role),
        joinedload(EModel.mtypes),
        joinedload(EModel.etypes),
        raiseload("*"),
    )


@router.get(
    "/{id_}",
)
def read_emodel(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
):
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=EModel,
        authorized_project_id=user_context.project_id,
        response_schema_class=EModelRead,
        apply_operations=load,
    )


@router.post("")
def create_emodel(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    emodel: EModelCreate,
):
    return router_create_one(
        db=db,
        authorized_project_id=user_context.project_id,
        db_model_class=EModel,
        json_model=emodel,
        response_schema_class=EModelRead,
        apply_operations=load,
        context_manager=ensure_authorized_references(
            "Exemplar morphology isn't public or owned by user"
        ),
    )


@router.get("")
def emodel_query(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    emodel_filter: EModelFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
):
    agent_alias = aliased(Agent, flat=True)
    morphology_alias = aliased(ReconstructionMorphology, flat=True)

    aliases = {
        Agent: agent_alias,
        ReconstructionMorphology: morphology_alias,
    }

    name_to_facet_query_params: dict[str, FacetQueryParams] = {
        "mtype": {"id": MTypeClass.id, "label": MTypeClass.pref_label},
        "etype": {"id": ETypeClass.id, "label": ETypeClass.pref_label},
        "species": {"id": Species.id, "label": Species.name},
        "contribution": {
            "id": agent_alias.id,
            "label": agent_alias.pref_label,
            "type": agent_alias.type,
        },
        "brain_region": {"id": BrainRegion.id, "label": BrainRegion.name},
        "exemplar_morphology": {
            "id": morphology_alias.id,
            "label": morphology_alias.name,
        },
    }

    def filter_query_operations(q: Select):
        return (
            q.join(Species, EModel.species_id == Species.id)
            .join(morphology_alias, EModel.exemplar_morphology_id == morphology_alias.id)
            .join(BrainRegion, EModel.brain_region_id == BrainRegion.id)
            .outerjoin(Contribution, EModel.id == Contribution.entity_id)
            .outerjoin(agent_alias, Contribution.agent_id == agent_alias.id)
            .outerjoin(MTypeClassification, EModel.id == MTypeClassification.entity_id)
            .outerjoin(MTypeClass, MTypeClass.id == MTypeClassification.mtype_class_id)
            .outerjoin(ETypeClassification, EModel.id == ETypeClassification.entity_id)
            .outerjoin(ETypeClass, ETypeClass.id == ETypeClassification.etype_class_id)
        )

    return router_read_many(
        db=db,
        db_model_class=EModel,
        user_context=user_context,
        with_search=with_search,
        facets=facets,
        aliases=aliases,
        apply_filter_query_operations=filter_query_operations,
        apply_data_query_operations=load,
        pagination_request=pagination_request,
        response_schema_class=ListResponse[EModelRead],
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=emodel_filter,
    )
