from app.db.types import (
    ALLOWED_ASSET_LABELS_PER_ENTITY,
    CONTENT_TYPE_TO_SUFFIX,
    EXTERNAL_SOURCE_INFO,
    ContentType,
    EntityType,
    ExternalSource,
)


def test_content_type_to_suffix():
    assert set(ContentType) == set(CONTENT_TYPE_TO_SUFFIX)


def test_allowed_asset_labels_per_entity():
    assert set(EntityType) == set(ALLOWED_ASSET_LABELS_PER_ENTITY)


def test_external_source_info():
    assert set(ExternalSource) == set(EXTERNAL_SOURCE_INFO)
