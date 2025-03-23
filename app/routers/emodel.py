import uuid

import sqlalchemy as sa
from fastapi import APIRouter
from sqlalchemy.orm import (
    aliased,
    joinedload,
    raiseload,
)
from sqlalchemy.sql.selectable import Select

from app.db.auth import constrain_to_accessible_entities
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
from app.dependencies.auth import VerifiedProjectContextHeader
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import (
    ensure_authorized_references,
    ensure_result,
)
from app.filters.emodel import EModelFilterDep
from app.routers.common import FacetQueryParams, FacetsDep, SearchDep
from app.schemas.emodel import EModelCreate, EModelRead
from app.schemas.types import ListResponse, PaginationResponse

router = APIRouter(
    prefix="/emodel",
    tags=["emodel"],
)


def emodel_joinedloads(select: Select):
    return select.options(
        joinedload(EModel.species),
        joinedload(EModel.strain),
        joinedload(EModel.exemplar_morphology),
        joinedload(EModel.brain_region),
        joinedload(EModel.contributions).joinedload(Contribution.agent),
        joinedload(EModel.contributions).joinedload(Contribution.role),
        joinedload(EModel.mtypes),
        joinedload(EModel.etypes),
        raiseload("*"),
    )


@router.get(
    "/{id_}",
)
def read_emodel(
    db: SessionDep,
    id_: uuid.UUID,
    project_context: VerifiedProjectContextHeader,
) -> EModelRead:
    with ensure_result("EModel not found"):
        query = constrain_to_accessible_entities(
            sa.select(EModel), project_context.project_id
        ).filter(EModel.id == id_)

        query = emodel_joinedloads(query)

        return db.execute(query).unique().scalar_one()


@router.post("", response_model=EModelRead)
def create_emodel(
    project_context: VerifiedProjectContextHeader,
    emodel: EModelCreate,
    db: SessionDep,
):
    with ensure_authorized_references("Exemplar morphology isn't public or owned by user"):
        db_em = EModel(
            name=emodel.name,
            description=emodel.description,
            brain_region_id=emodel.brain_region_id,
            species_id=emodel.species_id,
            strain_id=emodel.strain_id,
            exemplar_morphology_id=emodel.exemplar_morphology_id,
            authorized_project_id=project_context.project_id,
            authorized_public=emodel.authorized_public,
        )

        db.add(db_em)
        db.commit()
        db.refresh(db_em)

        query = emodel_joinedloads(sa.select(EModel).filter(EModel.id == db_em.id))
        return db.execute(query).unique().scalar_one()


@router.get("")
def emodel_query(
    *,
    db: SessionDep,
    project_context: VerifiedProjectContextHeader,
    pagination_request: PaginationQuery,
    emodel_filter: EModelFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
) -> ListResponse[EModelRead]:
    agent_alias = aliased(Agent, flat=True)
    morphology_alias = aliased(ReconstructionMorphology, flat=True)

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

    filter_query = (
        constrain_to_accessible_entities(sa.select(EModel), project_id=project_context.project_id)
        .join(Species, EModel.species_id == Species.id)
        .join(morphology_alias, EModel.exemplar_morphology_id == morphology_alias.id)
        .join(BrainRegion, EModel.brain_region_id == BrainRegion.id)
        .outerjoin(Contribution, EModel.id == Contribution.entity_id)
        .outerjoin(agent_alias, Contribution.agent_id == agent_alias.id)
        .outerjoin(MTypeClassification, EModel.id == MTypeClassification.entity_id)
        .outerjoin(MTypeClass, MTypeClass.id == MTypeClassification.mtype_class_id)
        .outerjoin(ETypeClassification, EModel.id == ETypeClassification.entity_id)
        .outerjoin(ETypeClass, ETypeClass.id == ETypeClassification.etype_class_id)
    )

    filter_query = emodel_filter.filter(
        filter_query,
        aliases={Agent: agent_alias, ReconstructionMorphology: morphology_alias},
    )
    filter_query = with_search(filter_query, EModel.description_vector)

    data_query = emodel_joinedloads(
        emodel_filter.sort(filter_query)
        .limit(pagination_request.page_size)
        .offset(pagination_request.offset)
        .distinct()
    )

    total_items = db.execute(
        filter_query.with_only_columns(sa.func.count(sa.func.distinct(EModel.id)).label("count"))
    ).scalar_one()

    response = ListResponse[EModelRead](
        data=db.execute(data_query).scalars().unique(),
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=facets(db, filter_query, name_to_facet_query_params, EModel.id),
    )

    return response
