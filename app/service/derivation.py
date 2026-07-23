"""Generic derivation service."""

import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING, cast

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload

from app.db.auth import constrain_to_writable_entities, is_public_or_in_projects
from app.db.model import Derivation, DerivationType, Entity, Person
from app.db.utils import ENTITY_TYPE_TO_CLASS
from app.dependencies.auth import AdminContextDep, UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import (
    ApiError,
    ApiErrorCode,
    ensure_result,
)
from app.filters.derivation import DerivationFilterDep
from app.filters.entity import BasicEntityFilterDep
from app.queries import crud
from app.queries.common import (
    router_create_one,
    router_read_many,
    router_read_one,
    router_update_one,
)
from app.queries.entity import get_accessible_entity, get_writable_entity
from app.queries.factory import query_params_factory
from app.queries.utils import is_user_authorized_for_deletion
from app.schemas.derivation import (
    DerivationAdminUpdate,
    DerivationCreate,
    DerivationRead,
    DerivationUserUpdate,
)
from app.schemas.entity import BasicEntityRead
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse
from app.types import EntityRoute
from app.utils.routers import entity_route_to_type

if TYPE_CHECKING:
    from app.filters.base import Aliases
    from app.schemas.auth import UserContext


def _load(query: sa.Select):
    return query.options(
        joinedload(Derivation.used, innerjoin=True),
        joinedload(Derivation.generated, innerjoin=True),
        joinedload(Derivation.created_by, innerjoin=True),
        joinedload(Derivation.updated_by, innerjoin=True),
        raiseload("*"),
    )


def _read_many(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: DerivationFilterDep,
    check_authorized_project: bool,
) -> ListResponse[DerivationRead]:

    project_ids = user_context.authorized_project_ids
    used_alias = aliased(Entity, flat=True, name="used_alias")
    generated_alias = aliased(Entity, flat=True, name="generated_alias")
    created_by_alias = aliased(Person, flat=True, name="created_by_alias")
    updated_by_alias = aliased(Person, flat=True, name="updated_by_alias")
    aliases: Aliases = {
        Entity: {"used": used_alias, "generated": generated_alias},
        Person: {"created_by": created_by_alias, "updated_by": updated_by_alias},
    }
    # `used`/`generated` are always joined below, so they are not declared here to
    # avoid duplicate joins. `created_by`/`updated_by` are added on demand.
    _, filter_joins = query_params_factory(
        db_model_class=Derivation,
        facet_keys=[],
        filter_keys=["created_by", "updated_by"],
        aliases=aliases,
    )

    def apply_filter_query_operations(q):
        q = q.join(used_alias, Derivation.used_id == used_alias.id).join(
            generated_alias, Derivation.generated_id == generated_alias.id
        )
        if check_authorized_project:
            q = q.where(
                is_public_or_in_projects(used_alias, project_ids),
                is_public_or_in_projects(generated_alias, project_ids),
            )
        return q

    return router_read_many(
        db=db,
        db_model_class=Derivation,
        authorized_project_id=user_context.project_id,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=aliases,
        apply_filter_query_operations=apply_filter_query_operations,
        apply_data_query_operations=_load,
        pagination_request=pagination_request,
        response_schema_class=DerivationRead,
        name_to_facet_query_params=None,
        filter_model=filter_model,
        filter_joins=filter_joins,
        check_authorized_project=False,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: DerivationFilterDep,
) -> ListResponse[DerivationRead]:
    return _read_many(
        user_context=user_context,
        db=db,
        pagination_request=pagination_request,
        filter_model=filter_model,
        check_authorized_project=True,
    )


def admin_read_many(
    user_context: AdminContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: DerivationFilterDep,
) -> ListResponse[DerivationRead]:
    return _read_many(
        user_context=user_context,
        db=db,
        pagination_request=pagination_request,
        filter_model=filter_model,
        check_authorized_project=False,
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> DerivationRead:
    project_ids = user_context.authorized_project_ids
    used_alias = aliased(Entity, flat=True, name="used_alias")
    generated_alias = aliased(Entity, flat=True, name="generated_alias")

    def apply_operations(q):
        q = q.join(used_alias, Derivation.used_id == used_alias.id).join(
            generated_alias, Derivation.generated_id == generated_alias.id
        )
        q = q.where(
            is_public_or_in_projects(used_alias, project_ids),
            is_public_or_in_projects(generated_alias, project_ids),
        )
        return _load(q)

    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=Derivation,
        user_context=None,
        response_schema_class=DerivationRead,
        apply_operations=apply_operations,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> DerivationRead:
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=Derivation,
        user_context=None,
        response_schema_class=DerivationRead,
        apply_operations=_load,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: DerivationUserUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> DerivationRead:
    def apply_operations(q):
        generated_alias = aliased(Entity, flat=True, name="generated_alias")
        q = q.join(generated_alias, Derivation.generated_id == generated_alias.id)
        q = constrain_to_writable_entities(
            query=q, user_context=user_context, db_model_class=generated_alias
        )
        return _load(q)

    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=Derivation,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=DerivationRead,
        apply_operations=apply_operations,
        check_authorized_project=False,  # checked with apply_operations
    )


def admin_update_one(
    user_context: AdminContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: DerivationAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
):
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=Derivation,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=DerivationRead,
        apply_operations=_load,
        check_authorized_project=False,
    )


def _read_many_from_entity(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    derivation_type: DerivationType,
    pagination_request: PaginationQuery,
    entity_filter: BasicEntityFilterDep,
    check_authorized_project: bool,
) -> ListResponse[BasicEntityRead]:
    """Return a list of basic entities used to generate the specified entity.

    Only the used entities that are accessible by the user are returned.
    """
    used_db_model_class = Entity
    generated_alias = aliased(Entity, flat=True, name="generated_alias")
    entity_type = entity_route_to_type(entity_route)
    generated_db_model_class = ENTITY_TYPE_TO_CLASS[entity_type]

    # ensure that the requested entity is readable
    if check_authorized_project:
        _ = get_accessible_entity(
            db,
            db_model_class=generated_db_model_class,
            entity_id=entity_id,
            user_context=user_context,
        )

    # always needed regardless of the filter, so it cannot go to filter_keys
    apply_filter_query_operations = lambda q: (
        q.join(Derivation, used_db_model_class.id == Derivation.used_id)
        .join(generated_alias, Derivation.generated_id == generated_alias.id)
        .where(
            generated_alias.id == entity_id,
            generated_alias.type == entity_type,
            Derivation.derivation_type == derivation_type,
        )
    )

    name_to_facet_query_params = filter_joins = None
    return router_read_many(
        db=db,
        db_model_class=used_db_model_class,
        authorized_project_id=user_context.project_id,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases={},
        apply_filter_query_operations=apply_filter_query_operations,
        apply_data_query_operations=None,
        pagination_request=pagination_request,
        response_schema_class=BasicEntityRead,
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=entity_filter,
        filter_joins=filter_joins,
        check_authorized_project=check_authorized_project,
    )


def read_many_from_entity(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    derivation_type: DerivationType,
    pagination_request: PaginationQuery,
    entity_filter: BasicEntityFilterDep,
) -> ListResponse[BasicEntityRead]:
    return _read_many_from_entity(
        user_context=user_context,
        db=db,
        entity_id=entity_id,
        entity_route=entity_route,
        derivation_type=derivation_type,
        pagination_request=pagination_request,
        entity_filter=entity_filter,
        check_authorized_project=True,
    )


def admin_read_many_from_entity(
    *,
    user_context: AdminContextDep,
    db: SessionDep,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    derivation_type: DerivationType,
    pagination_request: PaginationQuery,
    entity_filter: BasicEntityFilterDep,
) -> ListResponse[BasicEntityRead]:
    return _read_many_from_entity(
        user_context=user_context,
        db=db,
        entity_id=entity_id,
        entity_route=entity_route,
        derivation_type=derivation_type,
        pagination_request=pagination_request,
        entity_filter=entity_filter,
        check_authorized_project=False,
    )


def create_one(
    db: SessionDep,
    json_model: DerivationCreate,
    user_context: UserContextWithProjectIdDep,
) -> DerivationRead:
    """Create a new derivation from a readable entity (used) to a writable entity (generated).

    Used entity: a readable entity (public in any project, or private in the same project).
    Generated entity: a writable entity (public or private, in the same project).

    Even when the parent (used) is private, the child (generated) can be either public or private.

    See also https://github.com/openbraininstitute/entitycore/issues/427
    """
    _used_entity = get_accessible_entity(
        db,
        Entity,
        json_model.used_id,
        user_context=cast("UserContext", user_context),
    )
    _generated_entity = get_writable_entity(
        db,
        Entity,
        json_model.generated_id,
        user_context.project_id,
    )
    return router_create_one(
        db=db,
        json_model=json_model,
        db_model_class=Derivation,
        response_schema_class=DerivationRead,
        user_context=user_context,
        apply_operations=_load,
    )


def delete_one(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> DeleteResponse:
    query = (
        sa.select(Derivation)
        .where(Derivation.id == id_)
        .options(joinedload(Derivation.generated, innerjoin=True), raiseload("*"))
    )

    with ensure_result(error_message="Derivation not found"):
        derivation = db.execute(query).unique().scalar_one()

    # User has the same deletion authorization as for the generated entity
    if not is_user_authorized_for_deletion(db, user_context, derivation.generated):
        raise ApiError(
            message="User is not authorized to access resource.",
            error_code=ApiErrorCode.ENTITY_FORBIDDEN,
            http_status_code=HTTPStatus.FORBIDDEN,
        )

    crud.delete_one(db=db, row=derivation)

    return DeleteResponse(id=id_)
