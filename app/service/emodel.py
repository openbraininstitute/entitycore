import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload, selectinload

from app.db.model import (
    Agent,
    BrainRegion,
    Contribution,
    EModel,
    ETypeClass,
    ETypeClassification,
    IonChannelModel,
    MTypeClass,
    MTypeClassification,
    ReconstructionMorphology,
    Species,
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
from app.filters.emodel import EModelFilterDep
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.schemas.emodel import EModelCreate, EModelRead, EModelReadExpanded
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(select: sa.Select[tuple[EModel]]):
    return select.options(
        joinedload(EModel.species),
        joinedload(EModel.strain),
        joinedload(EModel.exemplar_morphology),
        joinedload(EModel.brain_region),
        selectinload(EModel.assets),
        selectinload(EModel.contributions).joinedload(Contribution.agent),
        selectinload(EModel.contributions).joinedload(Contribution.role),
        joinedload(EModel.mtypes),
        joinedload(EModel.etypes),
        selectinload(EModel.assets),
        selectinload(EModel.ion_channel_models).joinedload(IonChannelModel.species),
        selectinload(EModel.ion_channel_models).joinedload(IonChannelModel.strain),
        selectinload(EModel.ion_channel_models).joinedload(IonChannelModel.brain_region),
        selectinload(EModel.ion_channel_models).selectinload(IonChannelModel.assets),
        joinedload(EModel.createdBy),
        joinedload(EModel.updatedBy),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> EModelReadExpanded:
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=EModel,
        authorized_project_id=user_context.project_id,
        response_schema_class=EModelReadExpanded,
        apply_operations=_load,
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    emodel: EModelCreate,
) -> EModelRead:
    return router_create_one(
        db=db,
        user_context=user_context,
        db_model_class=EModel,
        json_model=emodel,
        response_schema_class=EModelRead,
        apply_operations=_load,
    )


def read_many(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    emodel_filter: EModelFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[EModelReadExpanded]:
    morphology_alias = aliased(ReconstructionMorphology, flat=True)
    agent_alias = aliased(Agent, flat=True)
    created_by_alias = aliased(Agent, flat=True)
    updated_by_alias = aliased(Agent, flat=True)
    aliases: Aliases = {
        ReconstructionMorphology: morphology_alias,
        Agent: {
            "contribution": agent_alias,
            "createdBy": created_by_alias,
            "updatedBy": updated_by_alias,
        },
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

    filter_joins = {
        "species": lambda q: q.join(Species, EModel.species_id == Species.id),
        "exemplar_morphology": lambda q: q.join(
            morphology_alias, EModel.exemplar_morphology_id == morphology_alias.id
        ),
        "brain_region": lambda q: q.join(BrainRegion, EModel.brain_region_id == BrainRegion.id),
        "contribution": lambda q: q.outerjoin(
            Contribution, EModel.id == Contribution.entity_id
        ).outerjoin(agent_alias, Contribution.agent_id == agent_alias.id),
        "mtype": lambda q: q.outerjoin(
            MTypeClassification, EModel.id == MTypeClassification.entity_id
        ).outerjoin(MTypeClass, MTypeClass.id == MTypeClassification.mtype_class_id),
        "etype": lambda q: q.outerjoin(
            ETypeClassification, EModel.id == ETypeClassification.entity_id
        ).outerjoin(ETypeClass, ETypeClass.id == ETypeClassification.etype_class_id),
        "createdBy": lambda q: q.outerjoin(
            created_by_alias, EModel.createdBy_id == created_by_alias.id
        ),
        "updatedBy": lambda q: q.outerjoin(
            updated_by_alias, EModel.updatedBy_id == updated_by_alias.id
        ),
    }

    return router_read_many(
        db=db,
        db_model_class=EModel,
        authorized_project_id=user_context.project_id,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        aliases=aliases,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        pagination_request=pagination_request,
        response_schema_class=EModelReadExpanded,
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=emodel_filter,
        filter_joins=filter_joins,
    )
