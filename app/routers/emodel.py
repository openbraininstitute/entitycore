from typing import Annotated, NotRequired, TypedDict

import sqlalchemy as sa
from fastapi import APIRouter
from fastapi_filter import FilterDepends
from sqlalchemy.orm import (
    InstrumentedAttribute,
    Session,
    aliased,
    joinedload,
    raiseload,
)

from app.db.model import (
    Agent,
    Contribution,
    EModel,
)
from http import HTTPStatus
from app.dependencies.auth import VerifiedProjectContextHeader
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.filters.emodel import EModelFilter
from app.schemas.emodel import EModelCreate, EModelRead
from app.schemas.types import Facet, Facets, ListResponse, PaginationResponse
from app.db.auth import constrain_to_accessible_entities
from app.errors import ApiError, ApiErrorCode

router = APIRouter(
    prefix="/emodel",
    tags=["emodel"],
)


class FacetQueryParams(TypedDict):
    id: InstrumentedAttribute[int]
    label: InstrumentedAttribute[str]
    type: NotRequired[InstrumentedAttribute[str]]


@router.get(
    "/{id_}",
)
def read_emodel(
    db: SessionDep,
    id_: int,
    # project_context: VerifiedProjectContextHeader,
) -> EModelRead:
    try:
        return emodel_query(
            db=db,
            pagination_request=PaginationQuery(page_size=1),
            emodel_filter=EModelFilter(id=id_),
        ).data[0]
    except IndexError as err:
        raise ApiError(
            message="EModel not found",
            error_code=ApiErrorCode.ENTITY_NOT_FOUND,
            http_status_code=HTTPStatus.NOT_FOUND,
        ) from err


@router.post("")
def create_emodel(
    project_context: VerifiedProjectContextHeader,
    emodel: EModelCreate,
    db: SessionDep,
) -> EModelRead:
    db_rm = EModel(
        name=emodel.name,
        description=emodel.description,
        brain_region_id=emodel.brain_region_id,
        species_id=emodel.species_id,
        strain_id=emodel.strain_id,
        authorized_project_id=project_context.project_id,
        authorized_public=emodel.authorized_public,
    )
    db.add(db_rm)
    db.commit()
    db.refresh(db_rm)

    return db_rm


def _get_facets(
    db: Session,
    query: sa.Select,
    name_to_facet_query_params: dict[str, FacetQueryParams],
    count_distinct_field: InstrumentedAttribute,
) -> Facets:
    facets = {}
    groupby_keys = ["id", "label", "type"]
    orderby_keys = ["label"]
    for facet_type, fields in name_to_facet_query_params.items():
        groupby_fields = {"type": sa.literal(facet_type), **fields}
        groupby_columns = [groupby_fields[key].label(key) for key in groupby_keys]  # type: ignore[attr-defined]
        groupby_ids = [sa.literal(i + 1) for i in range(len(groupby_columns))]
        facet_q = (
            query.with_only_columns(
                *groupby_columns,
                sa.func.count(sa.func.distinct(count_distinct_field)).label("count"),
            )
            .group_by(*groupby_ids)
            .order_by(*orderby_keys)
        )
        facets[facet_type] = [
            Facet.model_validate(row, from_attributes=True)
            for row in db.execute(facet_q).all()
            if row.id is not None  # exclude null rows if present
        ]

    return facets


@router.get("")
def emodel_query(
    *,
    db: SessionDep,
    # project_context: VerifiedProjectContextHeader,
    pagination_request: PaginationQuery,
    emodel_filter: Annotated[EModelFilter, FilterDepends(EModelFilter)],
    # search: str | None = None,
    # with_facets: bool = False,
) -> ListResponse[EModelRead]:
    agent_alias = aliased(Agent, flat=True)
    # name_to_facet_query_params: dict[str, FacetQueryParams] = {
    #     "mtype": {"id": MTypeClass.id, "label": MTypeClass.pref_label},
    #     "species": {"id": Species.id, "label": Species.name},
    #     "strain": {"id": Strain.id, "label": Strain.name},
    #     "contribution": {
    #         "id": agent_alias.id,
    #         "label": agent_alias.pref_label,
    #         "type": agent_alias.type,
    #     },
    # }

    # filter_query = (
    #     # constrain_to_accessible_entities(sa.select(EModel), project_id=project_context.project_id)
    #     sa.select(EModel)
    #     .join(Species, EModel.species_id == Species.id)
    #     .join(
    #         ReconstructionMorphology, EModel.exemplar_morphology_id == ReconstructionMorphology.id
    #     )
    #     .outerjoin(Strain, EModel.strain_id == Strain.id)
    #     .outerjoin(Contribution, EModel.id == Contribution.entity_id)
    #     .outerjoin(agent_alias, Contribution.agent_id == agent_alias.id)
    #     .outerjoin(MTypeClassification, EModel.id == MTypeClassification.entity_id)
    #     .outerjoin(MTypeClass, MTypeClass.id == MTypeClassification.mtype_class_id)
    #     .outerjoin(ETypeClassification, EModel.id == ETypeClassification.entity_id)
    #     .outerjoin(ETypeClass, ETypeClass.id == ETypeClassification.etype_class_id)
    # )

    # TODO: load person.* and organization.* eagerly

    # query = constrain_to_accessible_entities(sa.Select(EModel), project_context.project_id)
    query = sa.Select(EModel)

    filter_query = (
        emodel_filter.filter(query)
        .options(joinedload(EModel.species, innerjoin=True))
        .options(joinedload(EModel.exemplar_morphology, innerjoin=True))
        .options(joinedload(EModel.strain))
        .options(joinedload(EModel.contributions).joinedload(Contribution.agent))
        .options(joinedload(EModel.contributions).joinedload(Contribution.role))
        .options(joinedload(EModel.mtypes))
        .options(joinedload(EModel.etypes))
        .options(joinedload(EModel.brain_region))
        .options(raiseload("*"))
    )

    # if search:
    #     filter_query = filter_query.where(
    #         EModel.morphology_description_vector.match(search)
    #     )

    # filter_query = emodel_filter.filter(filter_query, aliases={Agent: agent_alias})

    # if with_facets:
    #     facets = _get_facets(
    #         db,
    #         filter_query,
    #         name_to_facet_query_params=name_to_facet_query_params,
    #         count_distinct_field=ReconstructionMorphology.id,
    #     )
    # else:
    #     facets = None

    # distinct_ids_subquery = (
    #     emodel_filter.sort(filter_query)
    #     .with_only_columns(EModel)
    #     .distinct()
    #     .offset(pagination_request.offset)
    #     .limit(pagination_request.page_size)
    # ).subquery("distinct_ids")

    # TODO: load person.* and organization.* eagerly
    # data_query = (
    #     emodel_filter.sort(sa.Select(EModel))  # sort without filtering
    #     .join(distinct_ids_subquery, EModel.id == distinct_ids_subquery.c.id)
    #     .options(joinedload(EModel.species, innerjoin=True))
    #     .options(joinedload(EModel.strain))
    #     .options(joinedload(EModel.contributions).joinedload(Contribution.agent))
    #     .options(joinedload(EModel.contributions).joinedload(Contribution.role))
    #     .options(joinedload(EModel.mtypes))
    #     .options(joinedload(EModel.etypes))
    #     .options(joinedload(EModel.brain_region))
    #     .options(joinedload(EModel.exemplar_morphology))
    #     .options(raiseload("*"))
    # )

    # unique is needed b/c it contains results that include joined eager loads against collections
    data = (
        db.execute(
            emodel_filter.sort(filter_query)
            .distinct()
            .limit(pagination_request.page_size)
            .offset(pagination_request.offset)
        )
        .scalars()
        .unique()
    )

    total_items = db.execute(
        filter_query.with_only_columns(sa.func.count(sa.func.distinct(EModel.id)).label("count"))
    ).scalar_one()

    response = ListResponse[EModelRead](
        data=data,
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )

    return response
