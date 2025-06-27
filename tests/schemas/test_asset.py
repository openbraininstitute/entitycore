from unittest.mock import Mock

import pytest

import app.schemas.asset as test_module
from app.db.types import ContentType, LabelRequirements


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
