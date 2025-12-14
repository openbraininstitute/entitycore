"""Generic derivation service."""

import uuid

import sqlalchemy as sa
from sqlalchemy import and_
from sqlalchemy.orm import aliased, joinedload, raiseload

from app.db.model import Derivation, DerivationType, Entity
from app.db.utils import ENTITY_TYPE_TO_CLASS, load_db_model_from_pydantic
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import DerivationQueryDep, PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import (
    ensure_authorized_references,
    ensure_foreign_keys_integrity,
    ensure_result,
    ensure_uniqueness,
)
from app.filters.entity import BasicEntityFilterDep
from app.queries.common import delete_row, router_read_many
from app.queries.entity import get_readable_entity, get_writable_entity
from app.schemas.base import BasicEntityRead
from app.schemas.derivation import DerivationCreate, DerivationRead
from app.schemas.types import ListResponse
from app.utils.routers import EntityRoute, entity_route_to_type


def read_many(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    derivation_type: DerivationType,
    pagination_request: PaginationQuery,
    entity_filter: BasicEntityFilterDep,
) -> ListResponse[BasicEntityRead]:
    """Return a list of basic entities used to generate the specified entity.

    Only the used entities that are accessible by the user are returned.
    """
    used_db_model_class = Entity
    generated_alias = aliased(Entity, flat=True, name="generated_alias")
    entity_type = entity_route_to_type(entity_route)
    generated_db_model_class = ENTITY_TYPE_TO_CLASS[entity_type]

    # ensure that the requested entity is readable
    _ = get_readable_entity(
        db,
        db_model_class=generated_db_model_class,
        entity_id=entity_id,
        project_id=user_context.project_id,
    )

    # always needed regardless of the filter, so it cannot go to filter_keys
    apply_filter_query_operations = (
        lambda q: q.join(Derivation, used_db_model_class.id == Derivation.used_id)
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
    used_entity = get_readable_entity(
        db,
        Entity,
        json_model.used_id,
        user_context.project_id,
    )
    generated_entity = get_writable_entity(
        db,
        Entity,
        json_model.generated_id,
        user_context.project_id,
    )
    db_model_class = Derivation
    db_model_instance = load_db_model_from_pydantic(
        json_model=json_model,
        db_model_class=db_model_class,
        authorized_project_id=None,
        created_by_id=None,
        updated_by_id=None,
    )

    with (
        ensure_foreign_keys_integrity("One or more foreign keys do not exist in the db"),
        ensure_uniqueness(f"{db_model_class.__name__} already exists or breaks unique constraints"),
        ensure_authorized_references(
            f"One of the entities referenced by {db_model_class.__name__} "
            f"is not public or not owned by the user"
        ),
    ):
        db.add(db_model_instance)
        db.flush()

    q = sa.select(db_model_class).where(
        and_(
            db_model_class.used_id == used_entity.id,
            db_model_class.generated_id == generated_entity.id,
        )
    )
    q = q.options(joinedload(Derivation.used), joinedload(Derivation.generated), raiseload("*"))
    db_model_instance = db.execute(q).unique().scalar_one()

    return DerivationRead.model_validate(db_model_instance)


def delete_one(
    *,
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    params: DerivationQueryDep,
) -> DerivationRead:
    used_entity = get_readable_entity(
        db,
        Entity,
        params.used_id,
        user_context.project_id,
    )
    generated_entity = get_writable_entity(
        db,
        Entity,
        params.generated_id,
        user_context.project_id,
    )
    db_model_class = Derivation

    q = sa.select(db_model_class).where(
        and_(
            db_model_class.used_id == used_entity.id,
            db_model_class.generated_id == generated_entity.id,
            db_model_class.derivation_type == params.derivation_type,
        )
    )
    with ensure_result(error_message=f"{db_model_class.__name__} not found"):
        obj = db.execute(q).scalars().one()

    delete_row(db=db, row=obj)

    return DerivationRead.model_validate(obj)
