import uuid

from app.db.model import MTypeClass
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.common import MTypeClassFilterDep
from app.queries.common import router_delete_one, router_read_many, router_read_one
from app.schemas.annotation import MTypeClassRead
from app.schemas.types import ListResponse


def read_many(
    db: SessionDep,
    pagination_request: PaginationQuery,
    mtype_class_filter: MTypeClassFilterDep,
) -> ListResponse[MTypeClassRead]:
    return router_read_many(
        db=db,
        db_model_class=MTypeClass,
        authorized_project_id=None,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=None,
        apply_filter_query_operations=None,
        apply_data_query_operations=None,
        pagination_request=pagination_request,
        response_schema_class=MTypeClassRead,
        name_to_facet_query_params=None,
        filter_model=mtype_class_filter,
    )


def read_one(id_: uuid.UUID, db: SessionDep) -> MTypeClassRead:
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=MTypeClass,
        authorized_project_id=None,
        response_schema_class=MTypeClassRead,
        apply_operations=None,
    )


def delete_one(
    _: AdminContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> MTypeClassRead:
    one = router_read_one(
        id_=id_,
        db=db,
        db_model_class=MTypeClass,
        authorized_project_id=None,
        response_schema_class=MTypeClassRead,
        apply_operations=None,
    )
    router_delete_one(
        id_=id_,
        db=db,
        db_model_class=MTypeClass,
        authorized_project_id=None,
    )
    return one
