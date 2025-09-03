import uuid
from typing import TYPE_CHECKING

from sqlalchemy.orm import (
    aliased,
    joinedload,
    raiseload,
    selectinload,
)
from sqlalchemy.sql.selectable import Select

from app.db.model import (
    Agent,
    Contribution,
    EModel,
    MEModel,
    MEModelCalibrationResult,
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
from app.filters.memodel import MEModelFilterDep
from app.queries.common import (
    router_create_one,
    router_read_many,
    router_read_one,
)
from app.queries.factory import query_params_factory
from app.schemas.me_model import MEModelCreate, MEModelRead
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(select: Select):
    return select.options(
        joinedload(MEModel.species),
        joinedload(MEModel.strain),
        joinedload(MEModel.emodel).options(
            joinedload(EModel.species),
            joinedload(EModel.strain),
            joinedload(EModel.exemplar_morphology),
            joinedload(EModel.brain_region),
            selectinload(EModel.contributions).joinedload(Contribution.agent),
            selectinload(EModel.contributions).joinedload(Contribution.role),
            joinedload(EModel.mtypes),
            joinedload(EModel.etypes),
            joinedload(EModel.created_by),
            joinedload(EModel.updated_by),
            selectinload(EModel.assets),
        ),
        joinedload(MEModel.morphology).options(
            joinedload(ReconstructionMorphology.brain_region),
            selectinload(ReconstructionMorphology.contributions).selectinload(Contribution.agent),
            selectinload(ReconstructionMorphology.contributions).selectinload(Contribution.role),
            joinedload(ReconstructionMorphology.mtypes),
            joinedload(ReconstructionMorphology.license),
            joinedload(ReconstructionMorphology.species),
            joinedload(ReconstructionMorphology.strain),
            joinedload(ReconstructionMorphology.created_by),
            joinedload(ReconstructionMorphology.updated_by),
            selectinload(ReconstructionMorphology.assets),
        ),
        joinedload(MEModel.brain_region),
        selectinload(MEModel.contributions).joinedload(Contribution.agent),
        selectinload(MEModel.contributions).joinedload(Contribution.role),
        joinedload(MEModel.mtypes),
        joinedload(MEModel.etypes),
        joinedload(MEModel.created_by),
        joinedload(MEModel.updated_by),
        joinedload(MEModel.calibration_result).joinedload(MEModelCalibrationResult.created_by),
        joinedload(MEModel.calibration_result).joinedload(MEModelCalibrationResult.updated_by),
        raiseload("*"),
    )


def read_one(db: SessionDep, id_: uuid.UUID, user_context: UserContextDep) -> MEModelRead:
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=MEModel,
        authorized_project_id=user_context.project_id,
        response_schema_class=MEModelRead,
        apply_operations=_load,
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    memodel: MEModelCreate,
    db: SessionDep,
) -> MEModelRead:
    return router_create_one(
        db=db,
        db_model_class=MEModel,
        user_context=user_context,
        response_schema_class=MEModelRead,
        json_model=memodel,
        apply_operations=_load,
    )


def read_many(
    *,
    db: SessionDep,
    user_context: UserContextDep,
    pagination_request: PaginationQuery,
    memodel_filter: MEModelFilterDep,
    search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[MEModelRead]:
    morphology_alias = aliased(ReconstructionMorphology, flat=True)
    emodel_alias = aliased(EModel, flat=True)
    agent_alias = aliased(Agent, flat=True)
    created_by_alias = aliased(Agent, flat=True)
    updated_by_alias = aliased(Agent, flat=True)

    aliases: Aliases = {
        ReconstructionMorphology: morphology_alias,
        EModel: emodel_alias,
        Agent: {
            "contribution": agent_alias,
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
        },
    }
    facet_keys = filter_keys = [
        "brain_region",
        "species",
        "morphology",
        "emodel",
        "created_by",
        "updated_by",
        "contribution",
        "mtype",
        "etype",
        "strain",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=MEModel,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        db_model_class=MEModel,
        authorized_project_id=user_context.project_id,
        with_search=search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        aliases=aliases,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        pagination_request=pagination_request,
        response_schema_class=MEModelRead,
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=memodel_filter,
        filter_joins=filter_joins,
    )
