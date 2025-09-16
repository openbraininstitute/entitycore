import uuid

import sqlalchemy as sa
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.auth import (
    constrain_to_accessible_entities,
    constrain_to_private_entities,
    select_unauthorized_entities,
)
from app.db.model import Activity, Agent, Generation, Identifiable, Person, Usage
from app.db.utils import get_declaring_class, load_db_model_from_pydantic
from app.dependencies.common import (
    FacetQueryParams,
    InBrainRegionQuery,
    PaginationQuery,
    Search,
    WithFacets,
)
from app.errors import (
    ensure_authorized_references,
    ensure_foreign_keys_integrity,
    ensure_result,
    ensure_uniqueness,
)
from app.filters.base import Aliases, CustomFilter
from app.queries.filter import filter_from_db
from app.queries.types import ApplyOperations
from app.schemas.activity import ActivityCreate, ActivityUpdate
from app.schemas.auth import UserContext, UserContextWithProjectId, UserProfile
from app.schemas.types import ListResponse, PaginationResponse
from app.utils.uuid import create_uuid


def router_read_one[T: BaseModel, I: Identifiable](
    *,
    id_: uuid.UUID,
    db: Session,
    db_model_class: type[I],
    authorized_project_id: uuid.UUID | None,
    response_schema_class: type[T],
    apply_operations: ApplyOperations[I] | None,
) -> T:
    """Read a model from the database.

    Args:
        id_: id of the entity to read.
        db: database session.
        db_model_class: database model class.
        authorized_project_id: id of the authorized project.
        response_schema_class: Pydantic schema class for the returned data.
        apply_operations: transformer function that modifies the select query.

    Returns:
        the model data as a Pydantic model.
    """
    query = sa.select(db_model_class).where(db_model_class.id == id_)
    if authorized_project_id and (
        id_model_class := get_declaring_class(db_model_class, "authorized_project_id")
    ):
        query = constrain_to_accessible_entities(
            query, authorized_project_id, db_model_class=id_model_class
        )
    if apply_operations:
        query = apply_operations(query)
    with ensure_result(error_message=f"{db_model_class.__name__} not found"):
        row = db.execute(query).unique().scalar_one()
    return response_schema_class.model_validate(row)


def router_create_activity_one[T: BaseModel, I: Activity](
    *,
    db: Session,
    db_model_class: type[I],
    user_context: UserContext | UserContextWithProjectId,
    json_model: ActivityCreate,
    response_schema_class: type[T],
    apply_operations: ApplyOperations | None = None,
):
    created_by_id = updated_by_id = project_id = None

    db_agent = get_or_create_user_agent(db, user_context.profile)
    created_by_id = updated_by_id = db_agent.id
    project_id = user_context.project_id

    # do not inlcude used_ids/generated_ids because they are relationships and need to be added in
    # the respective Usage/Generation tables
    db_model_instance = load_db_model_from_pydantic(
        json_model,
        db_model_class,
        created_by_id=created_by_id,
        updated_by_id=updated_by_id,
        authorized_project_id=project_id,
        ignore_attributes={"used_ids", "generated_ids"},
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

    if associated_ids := json_model.used_ids + json_model.generated_ids:
        if (
            unaccessible_entities := db.execute(
                select_unauthorized_entities(associated_ids, user_context.project_id)
            )
            .scalars()
            .all()
        ):
            raise HTTPException(
                status_code=404,
                detail=f"Cannot access entities {', '.join(str(e) for e in unaccessible_entities)}",
            )

        for entity_id in json_model.used_ids:
            db.add(Usage(usage_entity_id=entity_id, usage_activity_id=db_model_instance.id))

        for entity_id in json_model.generated_ids:
            db.add(
                Generation(
                    generation_entity_id=entity_id, generation_activity_id=db_model_instance.id
                )
            )

        db.flush()

    if apply_operations:
        q = sa.select(db_model_class).where(db_model_class.id == db_model_instance.id)
        q = apply_operations(q)
        db_model_instance = db.execute(q).unique().scalar_one()
    else:
        db.refresh(db_model_instance)
    return response_schema_class.model_validate(db_model_instance)


def router_create_one[T: BaseModel, I: Identifiable](
    *,
    db: Session,
    db_model_class: type[I],
    user_context: UserContext | UserContextWithProjectId,
    json_model: BaseModel,
    response_schema_class: type[T],
    apply_operations: ApplyOperations | None = None,
    embedding: list[float] | None = None,
) -> T:
    """Create a model in the database.

    Args:
        db: database session.
        db_model_class: database model class.
        user_context: the user context with project id and user information.
        json_model: instance of the Pydantic model.
        response_schema_class: Pydantic schema class for the returned data.
        apply_operations: transformer function that modifies the select query.
        embedding: optional embedding vector to attach to the model.

    Returns:
        the written model data as a Pydantic model.
    """
    created_by_id = updated_by_id = project_id = None

    db_agent = get_or_create_user_agent(db, user_context.profile)
    created_by_id = updated_by_id = db_agent.id

    project_id = (
        user_context.project_id
        if get_declaring_class(db_model_class, "authorized_project_id")
        else None
    )

    db_model_instance = load_db_model_from_pydantic(
        json_model,
        db_model_class,
        created_by_id=created_by_id,
        updated_by_id=updated_by_id,
        authorized_project_id=project_id,
    )

    if embedding is not None and hasattr(db_model_instance, "embedding"):
        db_model_instance.embedding = embedding  # type: ignore[attr-defined]

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

    if apply_operations:
        q = sa.select(db_model_class).where(db_model_class.id == db_model_instance.id)
        q = apply_operations(q)
        db_model_instance = db.execute(q).unique().scalar_one()
    else:
        db.refresh(db_model_instance)
    return response_schema_class.model_validate(db_model_instance)


def get_or_create_user_agent(db: Session, user_profile: UserProfile) -> Agent:
    query = sa.select(Person).where(Person.sub_id == user_profile.subject)

    if db_agent := db.execute(query).scalars().first():
        return db_agent

    agent_id = create_uuid()

    db_agent = Person(
        id=agent_id,
        pref_label=user_profile.name,
        given_name=user_profile.given_name,
        family_name=user_profile.family_name,
        sub_id=user_profile.subject,
        created_by_id=agent_id,
        updated_by_id=agent_id,
    )

    db.add(db_agent)
    db.flush()

    return db_agent


def router_read_many[T: BaseModel, I: Identifiable](  # noqa: PLR0913
    *,
    db: Session,
    db_model_class: type[I],
    authorized_project_id: uuid.UUID | None,
    with_search: Search[I] | None,
    with_in_brain_region: InBrainRegionQuery | None,
    facets: WithFacets | None,
    aliases: Aliases | None,
    apply_filter_query_operations: ApplyOperations[I] | None,
    apply_data_query_operations: ApplyOperations[I] | None,
    pagination_request: PaginationQuery,
    response_schema_class: type[T],
    name_to_facet_query_params: dict[str, FacetQueryParams] | None,
    filter_model: CustomFilter[I],
    filter_joins: dict[str, ApplyOperations] | None = None,
    embedding: list[float] | None = None,
) -> ListResponse[T]:
    """Read multiple models from the database.

    Args:
        db: database session.
        db_model_class: database model class.
        authorized_project_id: project id for filtering the resources.
        with_search: search query (str).
        with_in_brain_region: enable family queries based on BrainRegion
        facets: facet query (bool).
        aliases: dict of table aliases for the filter query.
        apply_filter_query_operations: optional callable to transform the filter query.
        apply_data_query_operations: optional callable to transform the data query.
        pagination_request: pagination.
        response_schema_class: Pydantic schema class for the returned data.
        name_to_facet_query_params: dict of FacetQueryParams for building the facets.
        filter_model: instance of CustomFilter for filtering and sorting data.
        filter_joins: mapping of filter names to join functions. The keys should match both:
            - the nested filters attributes, to choose which joins should be applied for filtering.
            - the keys in `name_to_facet_query_params`, for retrieving the facets.
        embedding: optional list of floats representing an embedding vector for semantic search.

    Returns:
        the list of model data, pagination, and facets as a Pydantic model.
    """
    filter_query = sa.select(db_model_class)
    if id_model_class := get_declaring_class(db_model_class, "authorized_project_id"):
        filter_query = constrain_to_accessible_entities(
            filter_query,
            project_id=authorized_project_id,
            db_model_class=id_model_class,
        )

    if apply_filter_query_operations:
        filter_query = apply_filter_query_operations(filter_query)

    if filter_joins:
        filter_query = filter_from_db(filter_query, filter_model, filter_joins)

    filter_query = filter_model.filter(filter_query, aliases=aliases)

    if with_search and (description_vector := getattr(db_model_class, "description_vector", None)):
        filter_query = with_search(filter_query, description_vector)

    if with_in_brain_region:
        filter_query = with_in_brain_region(filter_query, db_model_class)

    data_query = (
        filter_model.sort(filter_query, aliases=aliases)
        .order_by(db_model_class.id)
        .with_only_columns(db_model_class)
        .offset(pagination_request.offset)
        .limit(pagination_request.page_size)
    )

    # Add semantic similarity ordering if embedding is provided and model has embedding field
    if embedding is not None and hasattr(db_model_class, "embedding"):
        # Remove existing ordering clauses
        data_query._order_by_clauses = ()  # noqa: SLF001

        # Order by L2 distance first, then by ID to guarantee uniqueness
        data_query = data_query.order_by(
            db_model_class.embedding.l2_distance(embedding),  # type: ignore[attr-defined]
            db_model_class.id,
        )

    if apply_data_query_operations:
        data_query = apply_data_query_operations(data_query)

    # unique is needed b/c it contains results that include joined eager loads against collections
    data = db.execute(data_query).scalars().unique()

    total_items = db.execute(
        filter_query.with_only_columns(
            sa.func.count(sa.func.distinct(db_model_class.id)).label("count")
        )
    ).scalar_one()

    facets_result = (
        facets(
            db,
            filter_query,
            name_to_facet_query_params,
            count_distinct_field=db_model_class.id,
            filter_model=filter_model,
            filter_joins=filter_joins,
        )
        if facets and name_to_facet_query_params
        else None
    )
    return ListResponse[response_schema_class](
        data=[response_schema_class.model_validate(row) for row in data],
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=facets_result,
    )


def router_update_one[T: BaseModel, I: Identifiable](
    *,
    id_: uuid.UUID,
    db: Session,
    db_model_class: type[I],
    user_context: UserContext,
    json_model: BaseModel,
    response_schema_class: type[T],
    apply_operations: ApplyOperations | None = None,
):
    query = (
        sa.select(db_model_class).where(db_model_class.id == id_).with_for_update(of=db_model_class)
    )
    if id_model_class := get_declaring_class(db_model_class, "authorized_project_id"):
        query = constrain_to_private_entities(query, user_context, db_model_class=id_model_class)
    if apply_operations:
        query = apply_operations(query)

    with ensure_result(error_message=f"{db_model_class.__name__} not found"):
        obj = db.execute(query).unique().scalar_one()

    # remove attributes with NOT_SET sentinel and leave only user set ones
    update_data = json_model.model_dump(exclude_defaults=True)

    for key, value in update_data.items():
        setattr(obj, key, value)

    db.flush()
    db.refresh(obj)

    return response_schema_class.model_validate(obj)


def router_delete_one[T: BaseModel, I: Identifiable](
    *,
    id_: uuid.UUID,
    db: Session,
    db_model_class: type[I],
    authorized_project_id: uuid.UUID | None,
) -> dict:
    """Delete a model from the database.

    Args:
        id_: id of the entity to read.
        db: database session.
        db_model_class: database model class.
        authorized_project_id: project id for filtering the resources.
    """
    query = sa.select(db_model_class).where(db_model_class.id == id_)
    if authorized_project_id and (
        id_model_class := get_declaring_class(db_model_class, "authorized_project_id")
    ):
        query = constrain_to_accessible_entities(
            query, authorized_project_id, db_model_class=id_model_class
        )

    with ensure_result(error_message=f"{db_model_class.__name__} not found"):
        obj = db.execute(query).scalars().one()

    with ensure_foreign_keys_integrity(
        error_message=(
            f"{db_model_class.__name__} cannot be deleted "
            f"because of foreign keys integrity violation"
        )
    ):
        # Use ORM delete in order to ensure that ondelete cascades are triggered in parents  when
        # subclasses are deleted as it is the case with Activity/SimulationGeneration.
        db.delete(obj)
        db.flush()

    return {"id": id_}


def router_update_activity_one[T: BaseModel, I: Activity](
    *,
    id_: uuid.UUID,
    db: Session,
    db_model_class: type[I],
    user_context: UserContext | UserContextWithProjectId,
    json_model: ActivityUpdate,
    response_schema_class: type[T],
    apply_operations: ApplyOperations | None = None,
) -> T:
    query = sa.select(db_model_class).where(db_model_class.id == id_)
    if id_model_class := get_declaring_class(db_model_class, "authorized_project_id"):
        query = constrain_to_accessible_entities(
            query, user_context.project_id, db_model_class=id_model_class
        )
    if apply_operations:
        query = apply_operations(query)

    with ensure_result(error_message=f"{db_model_class.__name__} not found"):
        obj = db.execute(query).unique().scalar_one()

    update_data = json_model.model_dump(
        exclude_unset=True,
        exclude_none=True,
        exclude_defaults=True,
        exclude={"used_ids", "generated_ids"},
    )

    for key, value in update_data.items():
        setattr(obj, key, value)

    if generated_ids := json_model.generated_ids:
        if obj.generated:
            raise HTTPException(
                status_code=404,
                detail="It is forbidden to update generated_ids if they exist.",
            )

        if (
            unaccessible_entities := db.execute(
                select_unauthorized_entities(generated_ids, user_context.project_id)
            )
            .scalars()
            .all()
        ):
            raise HTTPException(
                status_code=404,
                detail=f"Cannot access entities {', '.join(str(e) for e in unaccessible_entities)}",
            )

        for entity_id in generated_ids:
            db.add(Generation(generation_entity_id=entity_id, generation_activity_id=obj.id))

    db.flush()
    db.refresh(obj)

    return response_schema_class.model_validate(obj)
