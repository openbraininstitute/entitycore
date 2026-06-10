from app.db.types import (
    ALLOWED_ASSET_LABELS_PER_ENTITY,
    ALLOWED_ASSET_LABELS_PER_TASK_RESULT,
    CONTENT_TYPE_TO_SUFFIX,
    EXTERNAL_SOURCE_INFO,
    ContentType,
    EntityType,
    ExternalSource,
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
