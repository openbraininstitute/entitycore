import pytest
from pydantic import ValidationError

from app.db.types import (
    ALLOWED_ASSET_LABELS_PER_ENTITY,
    ALLOWED_ASSET_LABELS_PER_TASK_RESULT,
    CONTENT_TYPE_TO_SUFFIX,
    EXTERNAL_SOURCE_INFO,
    ContentType,
    EntityType,
    ExternalSource,
    LabelRequirements,
    TaskResultType,
)


def test_content_type_to_suffix():
    assert set(ContentType) == set(CONTENT_TYPE_TO_SUFFIX)


def test_allowed_asset_labels_per_entity():
    assert set(EntityType) == set(ALLOWED_ASSET_LABELS_PER_ENTITY)


def test_allowed_asset_labels_per_task_result_type():
    assert set(TaskResultType) == set(ALLOWED_ASSET_LABELS_PER_TASK_RESULT)


def test_external_source_info():
    assert set(ExternalSource) == set(EXTERNAL_SOURCE_INFO)


def test_label_requirements_directory_content_type():
    LabelRequirements(content_type=None, is_directory=True)
    LabelRequirements(content_type=ContentType.json, is_directory=False)

    with pytest.raises(
        ValidationError, match="content_type must be None when is_directory is True"
    ):
        LabelRequirements(content_type=ContentType.json, is_directory=True)

    with pytest.raises(
        ValidationError, match="content_type must be None when is_directory is True"
    ):
        LabelRequirements(content_type=ContentType.directory, is_directory=True)
