import uuid

from fastapi import APIRouter

from app.db.utils import RESOURCE_TYPE_TO_CLASS
from app.dependencies.auth import AdminContextDep
from app.dependencies.db import SessionDep
from app.queries.common import router_delete_one
from app.utils.routers import ResourceRoute, route_to_type

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@router.delete("/{route}/{id_}")
def delete_one(
    _: AdminContextDep,
    db: SessionDep,
    route: ResourceRoute,
    id_: uuid.UUID,
):
    resource_type = route_to_type(route)
    return router_delete_one(
        id_=id_,
        db=db,
        db_model_class=RESOURCE_TYPE_TO_CLASS[resource_type],
        authorized_project_id=None,
    )
