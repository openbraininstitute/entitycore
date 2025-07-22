import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload, selectinload

from app.db.model import (
    Agent,
    Contribution,
    EModel,
    IonChannelModel,
    ReconstructionMorphology,
)
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.emodel import EModelFilterDep
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.queries.factory import query_params_factory
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
        selectinload(EModel.ion_channel_models).joinedload(IonChannelModel.subject),
        selectinload(EModel.ion_channel_models).joinedload(IonChannelModel.brain_region),
        selectinload(EModel.ion_channel_models).selectinload(IonChannelModel.assets),
        joinedload(EModel.created_by),
        joinedload(EModel.updated_by),
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
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
        },
    }
    facet_keys = filter_keys = [
        "brain_region",
        "species",
        "exemplar_morphology",
        "created_by",
        "updated_by",
        "contribution",
        "mtype",
        "etype",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=EModel,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
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
