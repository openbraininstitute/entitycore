import uuid
from http import HTTPStatus

import sqlalchemy as sa
from fastapi import APIRouter
from sqlalchemy.exc import InternalError
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
    MEModel,
    Strain,
)
from app.dependencies.auth import VerifiedProjectContextHeader
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ApiError, ApiErrorCode, ensure_result
from app.filters.emodel import EModelFilterDep
from app.routers.common import FacetQueryParams, FacetsDep, SearchDep
from app.schemas.emodel import EModelCreate
from app.schemas.me_model import MEModelRead, MEModelCreate
from app.schemas.types import ListResponse, PaginationResponse

router = APIRouter(
    prefix="/memodel",
    tags=["memodel"],
)


def memodel_joinedloads(select: Select):
    return select.options(
        joinedload(MEModel.species),
        joinedload(MEModel.strain),
        joinedload(MEModel.emodel),
        joinedload(MEModel.mmodel),
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
def read_memodel(
    db: SessionDep,
    id_: uuid.UUID,
    project_context: VerifiedProjectContextHeader,
) -> MEModelRead:
    with ensure_result("MEModel not found"):
        query = constrain_to_accessible_entities(
            sa.select(MEModel), project_context.project_id
        ).filter(MEModel.id == id_)

        query = memodel_joinedloads(query)

        return db.execute(query).unique().scalar_one()


@router.post("", response_model=MEModelRead)
def create_emodel(
    project_context: VerifiedProjectContextHeader,
    memodel: MEModelCreate,
    db: SessionDep,
):
    try:
        db_em = MEModel(
            name=memodel.name,
            description=memodel.description,
            brain_region_id=memodel.brain_region_id,
            species_id=memodel.species_id,
            strain_id=memodel.strain_id,
            emodel_id=memodel.emodel_id,
            mmodel_id=memodel.mmodel_id,
            authorized_project_id=project_context.project_id,
            authorized_public=memodel.authorized_public,
            validation_status=memodel.validation_status,
        )

        db.add(db_em)
        db.commit()
        db.refresh(db_em)

        query = memodel_joinedloads(sa.select(MEModel).filter(MEModel.id == db_em.id))
        return db.execute(query).unique().scalar_one()

    except InternalError as err:
        raise ApiError(
            message="Exemplar morphology isn't public or owned by user",
            error_code=ApiErrorCode.INVALID_REQUEST,
            http_status_code=HTTPStatus.FORBIDDEN,
        ) from err


@router.get("")
def memodel_query(
    *,
    db: SessionDep,
    project_context: VerifiedProjectContextHeader,
    pagination_request: PaginationQuery,
    # emodel_filter: EModelFilterDep,
    # with_search: SearchDep,
    facets: FacetsDep,
) -> ListResponse[MEModelRead]:
    agent_alias = aliased(Agent, flat=True)
    morphology_alias = aliased(ReconstructionMorphology, flat=True)
    emodel_alias = aliased(EModel, flat=True)

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
        "mmodel": {
            "id": morphology_alias.id,
            "label": morphology_alias.name,
        },
        "emodel": {
            "id": emodel_alias.id,
            "label": emodel_alias.name,
        },
    }

    filter_query = (
        constrain_to_accessible_entities(sa.select(MEModel), project_id=project_context.project_id)
        .outerjoin(Species, MEModel.species_id == Species.id)
        .outerjoin(Strain, MEModel.strain_id == Strain.id)
        .outerjoin(morphology_alias, MEModel.mmodel_id == morphology_alias.id)
        .outerjoin(emodel_alias, MEModel.emodel_id == emodel_alias.id)
        .outerjoin(BrainRegion, MEModel.brain_region_id == BrainRegion.id)
        .outerjoin(Contribution, MEModel.id == Contribution.entity_id)
        .outerjoin(agent_alias, Contribution.agent_id == agent_alias.id)
        .outerjoin(MTypeClassification, MEModel.id == MTypeClassification.entity_id)
        .outerjoin(MTypeClass, MTypeClass.id == MTypeClassification.mtype_class_id)
        .outerjoin(ETypeClassification, MEModel.id == ETypeClassification.entity_id)
        .outerjoin(ETypeClass, ETypeClass.id == ETypeClassification.etype_class_id)
    )

    # filter_query = emodel_filter.filter(
    #     filter_query,
    #     aliases={Agent: agent_alias, ReconstructionMorphology: morphology_alias},
    # )
    # filter_query = with_search(filter_query, EModel.description_vector)

    # data_query = emodel_joinedloads(emodel_filter.sort(filter_query).distinct())

    response = ListResponse[MEModelRead](
        # data=pagination_request.paginated_rows(db, data_query).scalars().unique(),
        data=[],
        # pagination=pagination_request.pagination(db, filter_query, EModel.id),
        pagination=PaginationResponse(page=0, page_size=0, total_items=0),
        facets=facets(db, filter_query, name_to_facet_query_params, MEModel.id),
    )

    return response
