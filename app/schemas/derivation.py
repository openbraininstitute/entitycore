import re
import uuid

from pydantic import BaseModel, ConfigDict, model_validator

from app.db.types import DerivationType
from app.schemas.base import BasicEntityRead

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


class DerivationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class DerivationCreate(DerivationBase):
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


class DerivationRead(DerivationBase):
    used: BasicEntityRead
    generated: BasicEntityRead
    derivation_type: DerivationType
    label: str | None = None
