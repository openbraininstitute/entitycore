import uuid

from app.db.model import License
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.license import LicenseFilterDep
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.schemas.base import LicenseCreate, LicenseRead
from app.schemas.types import ListResponse


def read_many(
    db: SessionDep, pagination_request: PaginationQuery, filter_model: LicenseFilterDep
) -> ListResponse[LicenseRead]:
    return router_read_many(
        db=db,
        db_model_class=License,
        authorized_project_id=None,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=None,
        apply_filter_query_operations=None,
        apply_data_query_operations=None,
        pagination_request=pagination_request,
        response_schema_class=LicenseRead,
        name_to_facet_query_params=None,
        filter_model=filter_model,
    )


def read_one(id_: uuid.UUID, db: SessionDep) -> LicenseRead:
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=License,
        authorized_project_id=None,
        response_schema_class=LicenseRead,
        apply_operations=None,
    )


def create_one(
    license: LicenseCreate, db: SessionDep, user_context: AdminContextDep
) -> LicenseRead:
    return router_create_one(
        db=db,
        db_model_class=License,
        json_model=license,
        response_schema_class=LicenseRead,
        user_context=user_context,
    )
