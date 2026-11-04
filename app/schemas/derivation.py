import uuid

from app.db.types import DERIVATION_TYPE_RULES, DerivationType, EntityType
from app.schemas.base import Schema
from app.schemas.entity import NestedEntityRead
from app.schemas.identifiable import IdentifiableCreate, IdentifiableRead
from app.schemas.utils import make_update_schema


class DerivationBase(Schema):
    pass


class DerivationCreate(DerivationBase, IdentifiableCreate):
    used_id: uuid.UUID
    generated_id: uuid.UUID
    derivation_type: DerivationType
    label: str | None = None


def validate_derivation_entity_types(
    derivation_type: DerivationType,
    used_type: EntityType,
    generated_type: EntityType,
) -> None:
    """Validate the types of the used and generated entities against the derivation type.

    Args:
        derivation_type: type of the derivation.
        used_type: type of the used entity.
        generated_type: type of the generated entity.

    Raises:
        ValueError: if any of the entity types is not allowed for the derivation type.
    """
    allowed = DERIVATION_TYPE_RULES[derivation_type]
    for role, entity_type, allowed_types in (
        ("used", used_type, allowed.used),
        ("generated", generated_type, allowed.generated),
    ):
        if allowed_types is not None and entity_type not in allowed_types:
            msg = (
                f"derivation_type '{derivation_type}' requires {role} entity type "
                f"to be one of {sorted(t.value for t in allowed_types)}, got '{entity_type}'"
            )
            raise ValueError(msg)


def validate_derivation_label(derivation_type: DerivationType, label: str | None) -> None:
    """Validate the label of a derivation against the derivation type.

    Args:
        derivation_type: type of the derivation.
        label: label of the derivation, or None if not set.

    Raises:
        ValueError: if the label is not allowed for the derivation type.
    """
    rule = DERIVATION_TYPE_RULES[derivation_type].label
    if label is None or rule is None:
        return
    if not rule.pattern.fullmatch(label):
        msg = f"label for derivation_type '{derivation_type}' must be {rule.description}"
        raise ValueError(msg)


# core attributes. Instead of changing them, the derivation should be deleted instead
DERIVATION_EXCLUDED_FIELDS = {"used_id", "generated_id", "derivation_type"}


DerivationUserUpdate = make_update_schema(
    DerivationCreate,
    "DerivationUserUpdate",
    excluded_fields=DERIVATION_EXCLUDED_FIELDS,
)  # pyright: ignore [reportInvalidTypeForm]
DerivationAdminUpdate = make_update_schema(
    DerivationCreate,
    "DerivationAdminUpdate",
    excluded_fields=DERIVATION_EXCLUDED_FIELDS,
)  # pyright: ignore [reportInvalidTypeForm]


class DerivationRead(DerivationBase, IdentifiableRead):
    used: NestedEntityRead
    generated: NestedEntityRead
    derivation_type: DerivationType
    label: str | None = None
