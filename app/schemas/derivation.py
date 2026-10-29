import re
import uuid

from pydantic import model_validator

from app.db.types import ALLOWED_ENTITY_TYPES_PER_DERIVATION_TYPE, DerivationType, EntityType
from app.schemas.base import Schema
from app.schemas.entity import NestedEntityRead
from app.schemas.identifiable import IdentifiableCreate, IdentifiableRead
from app.schemas.utils import make_update_schema

# Allowed label values per derivation type.
# - emodel_circuit: SONATA ``model_template`` entry, by convention ``hoc:<template_name>``.
# - circuit_customization: type of customization applied to the source circuit.
_HOC_TEMPLATE_RE = re.compile(r"^hoc:[A-Za-z0-9_]+$")
_CIRCUIT_CUSTOMIZATION_LABELS = frozenset(
    {
        "synaptic_modification",
        "emodel_addition",
        "emodel_modification",
        "population_modification",
    }
)


class DerivationBase(Schema):
    pass


class DerivationCreate(DerivationBase, IdentifiableCreate):
    used_id: uuid.UUID
    generated_id: uuid.UUID
    derivation_type: DerivationType
    label: str | None = None

    @model_validator(mode="after")
    def label_matches_derivation_type(self):
        """Validate the label against the derivation type when provided."""
        if self.label is None:
            return self
        if self.derivation_type == DerivationType.emodel_circuit and not _HOC_TEMPLATE_RE.fullmatch(
            self.label
        ):
            msg = (
                "label for derivation_type 'emodel_circuit' must match "
                "'hoc:<template_name>' (e.g. 'hoc:cADpyr_L5TPC')"
            )
            raise ValueError(msg)
        if (
            self.derivation_type == DerivationType.circuit_customization
            and self.label not in _CIRCUIT_CUSTOMIZATION_LABELS
        ):
            msg = (
                "label for derivation_type 'circuit_customization' must be one of "
                f"{sorted(_CIRCUIT_CUSTOMIZATION_LABELS)}"
            )
            raise ValueError(msg)
        return self


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

    Example:
        >>> validate_derivation_entity_types(
        ...     DerivationType.circuit_extraction, EntityType.circuit, EntityType.circuit
        ... )
    """
    allowed = ALLOWED_ENTITY_TYPES_PER_DERIVATION_TYPE[derivation_type]
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
