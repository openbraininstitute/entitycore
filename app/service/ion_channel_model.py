import uuid

from sqlalchemy.orm import joinedload, raiseload, selectinload

from app.db.model import Contribution, IonChannelModel, Species
from app.dependencies.auth import UserContextDep
from app.dependencies.common import PaginationQuery, SearchDep
from app.dependencies.db import SessionDep
from app.filters.ion_channel_model import IonChannelModelFilterDep
from app.queries.common import router_read_many, router_read_one
from app.schemas.ion_channel_model import (
    IonChannelModel as IonChannelModelRead,
    IonChannelModelExpanded,
)
from app.schemas.types import ListResponse, Select


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    with_search: SearchDep,
    icm_filter: IonChannelModelFilterDep,
) -> ListResponse[IonChannelModelRead]:
    def filter_query_ops(q: Select[IonChannelModel]):
        return q.join(Species, IonChannelModel.species_id == Species.id)

    def data_query_ops(q: Select[IonChannelModel]):
        return (
            q.options(joinedload(IonChannelModel.species, innerjoin=True))
            .options(joinedload(IonChannelModel.strain))
            .options(joinedload(IonChannelModel.brain_region))
            .options(raiseload("*"))
        )

    return router_read_many(
        db=db,
        db_model_class=IonChannelModel,
        authorized_project_id=user_context.project_id,
        with_search=with_search,
        facets=None,
        aliases=None,
        apply_data_query_operations=data_query_ops,
        apply_filter_query_operations=filter_query_ops,
        pagination_request=pagination_request,
        response_schema_class=IonChannelModelRead,
        name_to_facet_query_params=None,
        filter_model=icm_filter,
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> IonChannelModelExpanded:
    def _load(q: Select[IonChannelModel]):
        return (
            q.options(joinedload(IonChannelModel.species, innerjoin=True))
            .options(joinedload(IonChannelModel.strain))
            .options(joinedload(IonChannelModel.brain_region))
            .options(selectinload(IonChannelModel.contributions).selectinload(Contribution.agent))
            .options(selectinload(IonChannelModel.contributions).selectinload(Contribution.role))
            .options(selectinload(IonChannelModel.assets))
            .options(raiseload("*"))
        )

    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=IonChannelModel,
        authorized_project_id=user_context.project_id,
        response_schema_class=IonChannelModelExpanded,
        apply_operations=_load,
    )


# def create_one(
#     user_context: UserContextWithProjectIdDep,
#     db: SessionDep,
#     ion_channel_model: IonChannelModelCreate,
# ) -> IonChannelModelRead:
#     row = IonChannelModel(**ion_channel_model.model_dump(exclude_unset=True))
#     row.project_id = user_context.project_id

#     db.add(row)
#     db.commit()
#     db.refresh(row)

#     return IonChannelModelRead.model_validate(row)
