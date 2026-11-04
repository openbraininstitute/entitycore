import re

import pytest

from app.db.types import (
    DERIVATION_TYPE_RULES,
    CircuitCustomizationLabel,
    DerivationType,
    EntityType,
)
from app.schemas.derivation import validate_derivation_entity_types, validate_derivation_label


def test_rules_defined_for_every_derivation_type():
    assert set(DERIVATION_TYPE_RULES) == set(DerivationType)


@pytest.mark.parametrize(
    ("derivation_type", "used_type", "generated_type"),
    [
        (DerivationType.circuit_customization, EntityType.circuit, EntityType.circuit),
        (DerivationType.circuit_extraction, EntityType.circuit, EntityType.circuit),
        (DerivationType.circuit_rewiring, EntityType.circuit, EntityType.circuit),
        (DerivationType.circuit_simplification, EntityType.circuit, EntityType.circuit),
        (DerivationType.emodel_circuit, EntityType.emodel, EntityType.circuit),
        (
            DerivationType.em_dense_reconstruction_dataset_cell_morphology,
            EntityType.em_dense_reconstruction_dataset,
            EntityType.cell_morphology,
        ),
        (DerivationType.research_log_input, EntityType.circuit, EntityType.research_log),
        (DerivationType.research_log_output, EntityType.emodel, EntityType.research_log),
        (DerivationType.unspecified, EntityType.emodel, EntityType.emodel),
        (DerivationType.unspecified, EntityType.circuit, EntityType.cell_morphology),
    ],
)
def test_validate_derivation_entity_types(derivation_type, used_type, generated_type):
    validate_derivation_entity_types(derivation_type, used_type, generated_type)


@pytest.mark.parametrize(
    ("derivation_type", "used_type", "generated_type", "role"),
    [
        (DerivationType.circuit_extraction, EntityType.emodel, EntityType.circuit, "used"),
        (DerivationType.circuit_simplification, EntityType.circuit, EntityType.emodel, "generated"),
        (DerivationType.emodel_circuit, EntityType.circuit, EntityType.circuit, "used"),
        (DerivationType.emodel_circuit, EntityType.emodel, EntityType.emodel, "generated"),
        (
            DerivationType.em_dense_reconstruction_dataset_cell_morphology,
            EntityType.circuit,
            EntityType.cell_morphology,
            "used",
        ),
        (
            DerivationType.research_log_input,
            EntityType.circuit,
            EntityType.circuit,
            "generated",
        ),
    ],
)
def test_validate_derivation_entity_types_raises(derivation_type, used_type, generated_type, role):
    with pytest.raises(ValueError, match=f"requires {role} entity type"):
        validate_derivation_entity_types(derivation_type, used_type, generated_type)


def test_validate_derivation_entity_types_message():
    expected = (
        "derivation_type 'emodel_circuit' requires used entity type "
        "to be one of ['emodel'], got 'circuit'"
    )
    with pytest.raises(ValueError, match=f"^{re.escape(expected)}$"):
        validate_derivation_entity_types(
            DerivationType.emodel_circuit, EntityType.circuit, EntityType.circuit
        )


@pytest.mark.parametrize(
    ("derivation_type", "label"),
    [
        (DerivationType.emodel_circuit, "hoc:cADpyr_L5TPC"),
        (DerivationType.emodel_circuit, None),
        *((DerivationType.circuit_customization, label) for label in CircuitCustomizationLabel),
        (DerivationType.circuit_extraction, "any label"),
        (DerivationType.unspecified, "any label"),
    ],
)
def test_validate_derivation_label(derivation_type, label):
    validate_derivation_label(derivation_type, label)


@pytest.mark.parametrize(
    ("derivation_type", "label"),
    [
        (DerivationType.emodel_circuit, "cADpyr_L5TPC"),
        (DerivationType.emodel_circuit, "hoc:"),
        (DerivationType.emodel_circuit, "nml:cADpyr_L5TPC"),
        (DerivationType.emodel_circuit, "hoc:cADpyr_L5TPC "),
        (DerivationType.circuit_customization, "unknown_modification"),
        (DerivationType.circuit_customization, "synaptic_modification_extra"),
        (DerivationType.circuit_customization, ""),
    ],
)
def test_validate_derivation_label_raises(derivation_type, label):
    with pytest.raises(ValueError, match=f"label for derivation_type '{derivation_type}' must be"):
        validate_derivation_label(derivation_type, label)


def test_validate_derivation_label_message():
    expected = (
        "label for derivation_type 'circuit_customization' must be one of "
        "['emodel_addition', 'emodel_modification', 'population_modification', "
        "'synaptic_modification']"
    )
    with pytest.raises(ValueError, match=f"^{re.escape(expected)}$"):
        validate_derivation_label(DerivationType.circuit_customization, "other")
