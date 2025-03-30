import uuid

import sqlalchemy as sa
from fastapi import APIRouter
from sqlalchemy.orm import (
    aliased,
    joinedload,
    raiseload,
    selectinload,
)
from sqlalchemy.sql.selectable import Select

from app.db.model import (
    Agent,
    BrainRegion,
    Contribution,
    EModel,
    ETypeClass,
    ETypeClassification,
    MEModel,
    MTypeClass,
    MTypeClassification,
    ReconstructionMorphology,
    Species,
    Strain,
)
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import FacetQueryParams, FacetsDep, PaginationQuery, SearchDep
from app.dependencies.db import SessionDep
from app.errors import ensure_authorized_references
from app.filters.memodel import MEModelFilterDep
from app.routers.common import router_create_one, router_read_many, router_read_one
from app.schemas.me_model import MEModelCreate, MEModelRead
from app.schemas.types import ListResponse

router = APIRouter(
    prefix="/memodel",
    tags=["memodel"],
)


def memodel_joinedloads(select: Select):
    return select.options(
        joinedload(MEModel.species),
        joinedload(MEModel.strain),
        joinedload(MEModel.emodel),
        joinedload(MEModel.morphology),
        joinedload(MEModel.brain_region),
        joinedload(MEModel.contributions).joinedload(Contribution.agent),
        joinedload(MEModel.contributions).joinedload(Contribution.role),
        joinedload(MEModel.mtypes),
        joinedload(MEModel.etypes),
        raiseload("*"),
    )


@router.get(
    "/{id_}",
)
def read_memodel(db: SessionDep, id_: uuid.UUID, user_context: UserContextDep):
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=MEModel,
        authorized_project_id=user_context.project_id,
        response_schema_class=MEModelRead,
        apply_operations=memodel_joinedloads,
    )


@router.post("")
def create_memodel(
    user_context: UserContextWithProjectIdDep,
    memodel: MEModelCreate,
    db: SessionDep,
):
    return router_create_one(
        db=db,
        db_model_class=MEModel,
        authorized_project_id=user_context.project_id,
        response_schema_class=MEModelRead,
        json_model=memodel,
        apply_operations=memodel_joinedloads,
        context_manager=ensure_authorized_references(
            "Either morphology or emodel is not public or not owned by the user"
        ),
    )


@router.get("")
def memodel_query(
    *,
    db: SessionDep,
    user_context: UserContextDep,
    pagination_request: PaginationQuery,
    memodel_filter: MEModelFilterDep,
    search: SearchDep,
    facets: FacetsDep,
) -> ListResponse[MEModelRead]:
    agent_alias = aliased(Agent, flat=True)
    morphology_alias = aliased(ReconstructionMorphology, flat=True)
    emodel_alias = aliased(EModel, flat=True)

    aliases = {
        Agent: agent_alias,
        ReconstructionMorphology: morphology_alias,
        EModel: emodel_alias,
    }

    name_to_facet_query_params: dict[str, FacetQueryParams] = {
        "mtype": {"id": MTypeClass.id, "label": MTypeClass.pref_label},
        "etype": {"id": ETypeClass.id, "label": ETypeClass.pref_label},
        "species": {"id": Species.id, "label": Species.name},
        "strain": {"id": Strain.id, "label": Strain.name},
        "contribution": {
            "id": agent_alias.id,
            "label": agent_alias.pref_label,
            "type": agent_alias.type,
        },
        "brain_region": {"id": BrainRegion.id, "label": BrainRegion.name},
        "morphology": {
            "id": morphology_alias.id,
            "label": morphology_alias.name,
        },
        "emodel": {
            "id": emodel_alias.id,
            "label": emodel_alias.name,
        },
    }

    def filter_query_operations(q: sa.Select):
        return (
            q.join(Species, MEModel.species_id == Species.id)
            .outerjoin(Strain, MEModel.strain_id == Strain.id)
            .join(morphology_alias, MEModel.morphology_id == morphology_alias.id)
            .join(emodel_alias, MEModel.emodel_id == emodel_alias.id)
            .join(BrainRegion, MEModel.brain_region_id == BrainRegion.id)
            .outerjoin(Contribution, MEModel.id == Contribution.entity_id)
            .outerjoin(agent_alias, Contribution.agent_id == agent_alias.id)
            .outerjoin(MTypeClassification, MEModel.id == MTypeClassification.entity_id)
            .outerjoin(MTypeClass, MTypeClassification.mtype_class_id == MTypeClass.id)
            .outerjoin(ETypeClassification, MEModel.id == ETypeClassification.entity_id)
            .outerjoin(ETypeClass, ETypeClassification.etype_class_id == ETypeClass.id)
        )

    def data_query_operations(q: sa.Select):
        return q.options(
            joinedload(MEModel.species),
            joinedload(MEModel.strain),
            joinedload(MEModel.emodel),
            joinedload(MEModel.morphology),
            joinedload(MEModel.brain_region),
            selectinload(MEModel.contributions).joinedload(Contribution.agent),
            selectinload(MEModel.contributions).joinedload(Contribution.role),
            joinedload(MEModel.mtypes),
            joinedload(MEModel.etypes),
            raiseload("*"),
        )

    return router_read_many(
        db=db,
        db_model_class=MEModel,
        user_context=user_context,
        with_search=search,
        facets=facets,
        aliases=aliases,
        apply_data_query_operations=data_query_operations,
        apply_filter_query_operations=filter_query_operations,
        pagination_request=pagination_request,
        response_schema_class=ListResponse[MEModelRead],
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=memodel_filter,
    )
