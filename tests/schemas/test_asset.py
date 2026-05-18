from unittest.mock import Mock

import pytest

import app.schemas.asset as test_module
from app.db.types import AssetLabel, ContentType, EntityType, LabelRequirements, StorageType
from app.schemas.asset import AssetCreate
from app.utils.uuid import create_uuid


def test__raise_on_label_requirement():
    asset = Mock(is_directory=False, content_type="application/json", path="foo/bar/baz.JSON")
    test_module._raise_on_label_requirement(
        asset,
        [
            LabelRequirements(content_type=ContentType.json, is_directory=False),
            LabelRequirements(content_type=ContentType.jpg, is_directory=False),
        ],
    )

    with pytest.raises(
        ValueError,
        match=r"implies one of the following content-types: \['application/nrrd', 'image/jpeg'\]",
    ):
        test_module._raise_on_label_requirement(
            asset,
            [
                LabelRequirements(content_type=ContentType.nrrd, is_directory=False),
                LabelRequirements(content_type=ContentType.jpg, is_directory=False),
            ],
        )

    # directory
    asset = Mock(is_directory=True, content_type=None, path="foo/bar/baz/")
    with pytest.raises(
        ValueError,
        match=r"implies one of the following content-types: \['application/nrrd'\]",
    ):
        test_module._raise_on_label_requirement(
            asset,
            [
                LabelRequirements(content_type=ContentType.nrrd, is_directory=False),
            ],
        )

    # directory
    asset = Mock(is_directory=False, content_type=ContentType.jpg, path="foo/bar/baz/")
    with pytest.raises(
        ValueError,
        match=r"The label requirement for directory does not match `is_directory`",
    ):
        test_module._raise_on_label_requirement(
            asset,
            [
                LabelRequirements(content_type=None, is_directory=True),
            ],
        )

    # jpeg can either end in jpg or jpeg
    asset = Mock(is_directory=False, content_type="image/jpeg", path="foo/bar/baz.jpg")
    test_module._raise_on_label_requirement(
        asset,
        [LabelRequirements(content_type=ContentType.jpg, is_directory=False)],
    )
    asset = Mock(is_directory=False, content_type="image/jpeg", path="foo/bar/baz.jpeg")
    test_module._raise_on_label_requirement(
        asset,
        [LabelRequirements(content_type=ContentType.jpg, is_directory=False)],
    )

    # suffix mismatch: content type matches requirement but suffix doesn't
    asset = Mock(is_directory=False, content_type="image/jpeg", path="foo/bar/baz.png")
    with pytest.raises(ValueError, match=r"Suffix for content-type .* does not match .png"):
        test_module._raise_on_label_requirement(
            asset,
            [LabelRequirements(content_type=ContentType.jpg, is_directory=False)],
        )


@pytest.mark.parametrize(
    ("input_path", "expected"),
    [
        ("foo.txt", "foo.txt"),
        ("sub/foo.txt", "sub/foo.txt"),
        ("deep/nested/folder/foo.txt", "deep/nested/folder/foo.txt"),
        (".../current_dir_file.txt", ".../current_dir_file.txt"),  # Triple dots
        ("..%2F..%2Fetc%2Fpasswd", "..%2F..%2Fetc%2Fpasswd"),  # URL encoded
    ],
)
def test_validate_relative_path_str(input_path, expected):
    assert test_module.validate_relative_path_str(input_path) == expected


@pytest.mark.parametrize(
    ("input_path", "expected_error"),
    [
        ("/etc/passwd", "Absolute paths are forbidden"),
        ("folder/../folder/file.txt", "Parent traversal is forbidden"),
        ("../etc/passwd", "Parent traversal is forbidden"),
        ("./../../../etc/passwd", "Parent traversal is forbidden"),
        ("../", "Parent traversal is forbidden"),
        ("", "Empty paths are forbidden"),
        (".", "Empty paths are forbidden"),
        ("./", "Empty paths are forbidden"),
        ("./current_dir_file.txt", "Path must be normalized"),
        ("folder/./current_dir_file.txt", "Path must be normalized"),
    ],
)
def test_validate_relative_path_str_raises(input_path, expected_error):
    with pytest.raises(ValueError, match=expected_error):
        test_module.validate_relative_path_str(input_path)


@pytest.mark.parametrize(
    ("input_path", "expected"),
    [
        ("foo.txt", "foo.txt"),
        ("..%2F..%2Fetc%2Fpasswd", "..%2F..%2Fetc%2Fpasswd"),  # URL encoded
    ],
)
def test_validate_path_component_str(input_path, expected):
    assert test_module.validate_path_component_str(input_path) == expected


@pytest.mark.parametrize(
    ("input_path", "expected_error"),
    [
        ("", "Expected a valid file or directory name"),
        (".", "Expected a valid file or directory name"),
        ("./", "Expected a valid file or directory name"),
        ("sub/foo.txt", "Expected a valid file or directory name"),
        ("../etc/passwd", "Expected a valid file or directory name"),
        ("/passwd", "Expected a valid file or directory name"),
        ("/", "Expected a valid file or directory name"),
        ("..", "Expected a valid file or directory name"),
        ("../", "Expected a valid file or directory name"),
        ("./current_dir_file.txt", "Name must be normalized"),
    ],
)
def test_validate_path_component_str_raises(input_path, expected_error):
    with pytest.raises(ValueError, match=expected_error):
        test_module.validate_path_component_str(input_path)


def test_asset_create_directory_child_without_parent_id():
    """directory_child label requires parent_id."""
    agent_id = create_uuid()
    with pytest.raises(ValueError, match="Directory child assets must have a parent_id"):
        AssetCreate(
            path="dir/file.bin",
            full_path="vlab/proj/dir/file.bin",
            is_directory=False,
            content_type=ContentType.other,
            size=100,
            sha256_digest="a" * 64,
            meta={},
            label=AssetLabel.directory_child,
            storage_type=StorageType.aws_s3_internal,
            entity_type=EntityType.circuit,
            parent_id=None,
            created_by_id=agent_id,
            updated_by_id=agent_id,
        )


def test_asset_create_directory_with_parent_id():
    """Directory assets cannot have a parent_id."""
    agent_id = create_uuid()
    parent_id = create_uuid()
    with pytest.raises(ValueError, match="Directories assets cannot have a parent_id"):
        AssetCreate(
            path="my-dir",
            full_path="vlab/proj/my-dir",
            is_directory=True,
            content_type=ContentType.directory,
            size=-1,
            sha256_digest=None,
            meta={},
            label=AssetLabel.directory_child,
            storage_type=StorageType.aws_s3_internal,
            entity_type=EntityType.circuit,
            parent_id=parent_id,
            created_by_id=agent_id,
            updated_by_id=agent_id,
        )
