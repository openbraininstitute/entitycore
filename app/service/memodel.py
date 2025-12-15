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
    CellMorphology,
    Contribution,
    EModel,
    MEModel,
    MEModelCalibrationResult,
    Person,
    Subject,
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
    router_update_one,
    router_user_delete_one,
)
from app.queries.factory import query_params_factory
from app.schemas.me_model import MEModelAdminUpdate, MEModelCreate, MEModelRead, MEModelUserUpdate
from app.schemas.routers import DeleteResponse
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
            joinedload(CellMorphology.brain_region),
            joinedload(CellMorphology.cell_morphology_protocol),
            selectinload(CellMorphology.contributions).selectinload(Contribution.agent),
            selectinload(CellMorphology.contributions).selectinload(Contribution.role),
            joinedload(CellMorphology.mtypes),
            joinedload(CellMorphology.license),
            joinedload(CellMorphology.subject).joinedload(Subject.species),
            joinedload(CellMorphology.subject).joinedload(Subject.strain),
            joinedload(CellMorphology.created_by),
            joinedload(CellMorphology.updated_by),
            selectinload(CellMorphology.assets),
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
        user_context=user_context,
        response_schema_class=MEModelRead,
        apply_operations=_load,
    )


def admin_read_one(db: SessionDep, id_: uuid.UUID) -> MEModelRead:
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=MEModel,
        user_context=None,
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


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: MEModelUserUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> MEModelRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=MEModel,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=MEModelRead,
        apply_operations=_load,
    )


def admin_update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: MEModelAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> MEModelRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=MEModel,
        user_context=None,
        json_model=json_model,
        response_schema_class=MEModelRead,
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
    morphology_alias = aliased(CellMorphology, flat=True)
    emodel_alias = aliased(EModel, flat=True)
    agent_alias = aliased(Agent, flat=True)
    created_by_alias = aliased(Person, flat=True)
    updated_by_alias = aliased(Person, flat=True)

    aliases: Aliases = {
        CellMorphology: morphology_alias,
        EModel: emodel_alias,
        Agent: {
            "contribution": agent_alias,
        },
        Person: {
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


def delete_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> DeleteResponse:
    return router_user_delete_one(
        id_=id_,
        db=db,
        db_model_class=MEModel,
        user_context=user_context,
    )
