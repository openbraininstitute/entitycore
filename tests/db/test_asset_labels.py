from unittest.mock import Mock

import pytest

from app.db.model import TaskResult
from app.db.types import (
    ALLOWED_ASSET_LABELS_PER_ENTITY,
    ALLOWED_ASSET_LABELS_PER_TASK_RESULT,
    AssetLabel,
    EntityType,
    TaskResultType,
)
from app.db.utils import allowed_asset_labels_for
from app.schemas.asset import validate_asset_label
from app.utils.uuid import create_uuid


def test_allowed_asset_labels_for_task_result_uses_result_type():
    entity = TaskResult(
        id=create_uuid(),
        type=EntityType.task_result,
        task_result_type=TaskResultType.circuit_extraction__circuit,
        authorized_project_id=create_uuid(),
        name="result",
        description="result",
    )
    allowed = allowed_asset_labels_for(entity)
    assert (
        allowed == ALLOWED_ASSET_LABELS_PER_TASK_RESULT[TaskResultType.circuit_extraction__circuit]
    )
    assert AssetLabel.sonata_circuit in allowed
    assert allowed != ALLOWED_ASSET_LABELS_PER_ENTITY[EntityType.task_result]


def test_allowed_asset_labels_for_non_resolved_entity():
    entity = Mock(type=EntityType.circuit)
    allowed = allowed_asset_labels_for(entity)
    assert allowed == ALLOWED_ASSET_LABELS_PER_ENTITY[EntityType.circuit]


def test_compartment_sets_asset_label_allowed_for_simulation():
    allowed = ALLOWED_ASSET_LABELS_PER_ENTITY[EntityType.simulation]

    assert AssetLabel.compartment_sets in allowed
    assert allowed[AssetLabel.compartment_sets][0].content_type == "application/json"


def test_validate_asset_label_rejects_label_not_allowed_for_task_result_type():
    asset = Mock(
        label=AssetLabel.morphology,
        entity_type=EntityType.task_result,
        parent_id=None,
        is_directory=False,
        content_type="application/asc",
        path="foo.asc",
    )
    allowed = ALLOWED_ASSET_LABELS_PER_TASK_RESULT[TaskResultType.circuit_extraction__circuit]
    with pytest.raises(ValueError, match="is not allowed for entity type"):
        validate_asset_label(asset, allowed)
