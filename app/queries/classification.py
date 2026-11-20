import uuid

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.model import ETypeClassification, MTypeClassification
from app.errors import ApiError, ApiErrorCode, ensure_foreign_keys_integrity, ensure_uniqueness
from app.queries.utils import get_or_create_user
from app.schemas.auth import UserContext, UserContextWithProjectId

MTYPE_CLASS_IDS_FIELD = "mtype_class_ids"
ETYPE_CLASS_IDS_FIELD = "etype_class_ids"
CLASSIFICATION_CREATE_FIELDS = frozenset({MTYPE_CLASS_IDS_FIELD, ETYPE_CLASS_IDS_FIELD})


def classification_create_ignore_attributes(json_model: BaseModel) -> set[str]:
    """Return classification create field names declared on the create schema."""
    return CLASSIFICATION_CREATE_FIELDS & json_model.__class__.model_fields.keys()


def create_mtype_classifications_for_entity(
    db: Session,
    *,
    entity_id: uuid.UUID,
    mtype_class_ids: list[uuid.UUID],
    user_context: UserContext | UserContextWithProjectId,
) -> None:
    """Create public mtype classifications for a newly created entity.

    Same rules as POST /mtype-classification: always authorized_public=True.
    """
    if not mtype_class_ids:
        return

    project_id = _require_project_id(user_context)
    db_user = get_or_create_user(db, user_context.profile)
    rows = [
        MTypeClassification(
            entity_id=entity_id,
            mtype_class_id=mtype_class_id,
            authorized_public=True,
            authorized_project_id=project_id,
            created_by_id=db_user.id,
            updated_by_id=db_user.id,
        )
        for mtype_class_id in dict.fromkeys(mtype_class_ids)
    ]

    with (
        ensure_foreign_keys_integrity("One or more foreign keys do not exist in the db"),
        ensure_uniqueness("Classification already exists or breaks unique constraints"),
    ):
        db.add_all(rows)
        db.flush()


def create_etype_classifications_for_entity(
    db: Session,
    *,
    entity_id: uuid.UUID,
    etype_class_ids: list[uuid.UUID],
    user_context: UserContext | UserContextWithProjectId,
) -> None:
    """Create public etype classifications for a newly created entity.

    Same rules as POST /etype-classification: always authorized_public=True.
    """
    if not etype_class_ids:
        return

    project_id = _require_project_id(user_context)
    db_user = get_or_create_user(db, user_context.profile)
    rows = [
        ETypeClassification(
            entity_id=entity_id,
            etype_class_id=etype_class_id,
            authorized_public=True,
            authorized_project_id=project_id,
            created_by_id=db_user.id,
            updated_by_id=db_user.id,
        )
        for etype_class_id in dict.fromkeys(etype_class_ids)
    ]

    with (
        ensure_foreign_keys_integrity("One or more foreign keys do not exist in the db"),
        ensure_uniqueness("Classification already exists or breaks unique constraints"),
    ):
        db.add_all(rows)
        db.flush()


def create_classifications_from_create_model(
    db: Session,
    *,
    entity_id: uuid.UUID,
    json_model: BaseModel,
    user_context: UserContext | UserContextWithProjectId,
) -> None:
    """Attach classifications for fields declared on the create schema."""
    fields = json_model.__class__.model_fields

    if MTYPE_CLASS_IDS_FIELD in fields:
        mtype_class_ids = getattr(json_model, MTYPE_CLASS_IDS_FIELD)
        if mtype_class_ids:
            create_mtype_classifications_for_entity(
                db,
                entity_id=entity_id,
                mtype_class_ids=mtype_class_ids,
                user_context=user_context,
            )

    if ETYPE_CLASS_IDS_FIELD in fields:
        etype_class_ids = getattr(json_model, ETYPE_CLASS_IDS_FIELD)
        if etype_class_ids:
            create_etype_classifications_for_entity(
                db,
                entity_id=entity_id,
                etype_class_ids=etype_class_ids,
                user_context=user_context,
            )


def _require_project_id(user_context: UserContext | UserContextWithProjectId) -> uuid.UUID:
    if user_context.project_id is None:
        raise ApiError(
            message="project-id is required to create classifications",
            error_code=ApiErrorCode.INVALID_REQUEST,
        )
    return user_context.project_id
