import uuid

from app.db.model import ETypeClass
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.common import ETypeClassFilterDep
from app.queries.common import router_read_many, router_read_one
from app.schemas.annotation import ETypeClassRead
from app.schemas.types import ListResponse


def read_many(
    db: SessionDep,
    pagination_request: PaginationQuery,
    etype_class_filter: ETypeClassFilterDep,
) -> ListResponse[ETypeClassRead]:
    return router_read_many(
        db=db,
        db_model_class=ETypeClass,
        authorized_project_id=None,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=None,
        apply_filter_query_operations=None,
        apply_data_query_operations=None,
        pagination_request=pagination_request,
        response_schema_class=ETypeClassRead,
        name_to_facet_query_params=None,
        filter_model=etype_class_filter,
    )


def read_one(id_: uuid.UUID, db: SessionDep) -> ETypeClassRead:
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=ETypeClass,
        authorized_project_id=None,
        response_schema_class=ETypeClassRead,
        apply_operations=None,
    )
