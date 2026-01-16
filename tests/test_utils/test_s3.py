import math
from pathlib import Path

import pytest

from app.config import settings
from app.db.types import EntityType
from app.utils import s3 as test_module

from tests.utils import PROJECT_ID, VIRTUAL_LAB_ID


def test_build_s3_path_private():
    entity_id = 123456
    result = test_module.build_s3_path(
        vlab_id=VIRTUAL_LAB_ID,
        proj_id=PROJECT_ID,
        entity_type=EntityType.cell_morphology,
        entity_id=entity_id,
        filename="a/b/c.txt",
        is_public=False,
    )
    assert result == (
        f"private/{VIRTUAL_LAB_ID}/{PROJECT_ID}/assets/cell_morphology/{entity_id}/a/b/c.txt"
    )


def test_build_s3_path_public():
    entity_id = 123456
    result = test_module.build_s3_path(
        vlab_id=VIRTUAL_LAB_ID,
        proj_id=PROJECT_ID,
        entity_type=EntityType.cell_morphology,
        entity_id=entity_id,
        filename="a/b/c.txt",
        is_public=True,
    )
    assert result == (
        f"public/{VIRTUAL_LAB_ID}/{PROJECT_ID}/assets/cell_morphology/{entity_id}/a/b/c.txt"
    )


def test_sanitize_directory_traversal():
    safe_paths = [
        ("foo.txt", "foo.txt"),
        ("sub/foo.txt", "sub/foo.txt"),
        ("deep/nested/folder/foo.txt", "deep/nested/folder/foo.txt"),
        ("./current_dir_file.txt", "current_dir_file.txt"),
        ("folder/../folder/file.txt", "folder/file.txt"),
    ]
    for p0, p1 in safe_paths:
        assert test_module.sanitize_directory_traversal(p0) == Path(p1)

    attack_paths = [
        ("../etc/passwd", "etc/passwd"),
        ("../../etc/passwd", "etc/passwd"),
        ("../../../etc/passwd", "etc/passwd"),
        ("../../../../../../../../etc/passwd", "etc/passwd"),
        ("./../../../etc/passwd", "etc/passwd"),
        ("folder/../../../../../../etc/passwd", "etc/passwd"),
        ("../", ""),
        ("/var/www/files/../../../etc/passwd", "etc/passwd"),
        (".../.../etc/passwd", ".../.../etc/passwd"),  # Triple dots
        # ("..%2F..%2Fetc%2Fpasswd",  # URL encoded
        # ("..%252F..%252Fetc%252Fpasswd",  # Double URL encoded
    ]
    for p0, p1 in attack_paths:
        assert test_module.sanitize_directory_traversal(p0) == Path(p1), f"`{p0}` failed"


@pytest.mark.parametrize(
    ("filesize", "preferred_part_count", "expected_part_size", "expected_part_count"),
    [
        # preferred count below min
        (
            50 * 1024**2,
            1,
            # clipped to min part count
            math.ceil(50 * 1024**2 / settings.S3_MULTIPART_UPLOAD_MIN_PARTS),
            settings.S3_MULTIPART_UPLOAD_MIN_PARTS,
        ),
        # preferred count above max
        (
            1024**4,
            300_000,
            # part count clipped to max parts
            math.ceil((1024**4) / settings.S3_MULTIPART_UPLOAD_MAX_PARTS),
            settings.S3_MULTIPART_UPLOAD_MAX_PARTS,
        ),
        # filesize smaller than min part size
        (
            settings.S3_MULTIPART_UPLOAD_MIN_PART_SIZE // 2,
            5,
            settings.S3_MULTIPART_UPLOAD_MIN_PART_SIZE,
            1,  # only one part needed
        ),
        # filesize larger than max part size (forces part count up)
        (
            settings.S3_MULTIPART_UPLOAD_MAX_PART_SIZE * 10 + 123,
            5,
            settings.S3_MULTIPART_UPLOAD_MAX_PART_SIZE,
            11,  # ceil(10 + 123 / max_part_size)
        ),
        # exact multiple of preferred part count
        (
            50 * 1024**2,
            5,
            math.ceil(50 * 1024 * 1024 / 5),
            5,
        ),
        # rounding up part size
        (
            50 * 1024**2 + 1,
            5,
            math.ceil((50 * 1024 * 1024 + 1) / 5),
            5,
        ),
        # small file, preferred part count large
        (
            1024**2,
            100,
            settings.S3_MULTIPART_UPLOAD_MIN_PART_SIZE,
            1,
        ),
        # huge file, preferred part count very small
        (
            500 * 1024**3,
            1,
            settings.S3_MULTIPART_UPLOAD_MAX_PART_SIZE,
            math.ceil(500 * 1024**3 / settings.S3_MULTIPART_UPLOAD_MAX_PART_SIZE),
        ),
    ],
    ids=[
        "preferred-count-below-min",
        "preferred-count-above-max",
        "filesize-smaller-min-part-size",
        "filesize-larger-max-part-size",
        "exact-multiple-of-preferred-part-count",
        "rounding-up-part-size",
        "small-file-preferred-part-count-large",
        "huge-file-preferred-part-count-very-small",
    ],
)
def test_multipart_compute_upload_plan(
    filesize, preferred_part_count, expected_part_size, expected_part_count
):
    part_size, part_count = test_module.multipart_compute_upload_plan(
        filesize=filesize, preferred_part_count=preferred_part_count
    )

    # check part count respects limits
    assert (
        settings.S3_MULTIPART_UPLOAD_MIN_PARTS
        <= part_count
        <= settings.S3_MULTIPART_UPLOAD_MAX_PARTS
    )

    # check part size respects limits
    assert (
        settings.S3_MULTIPART_UPLOAD_MIN_PART_SIZE
        <= part_size
        <= settings.S3_MULTIPART_UPLOAD_MAX_PART_SIZE
    )

    # check computed values match expectation
    assert part_size == expected_part_size
    assert part_count == expected_part_count

    # sanity check: all parts cover the full filesize
    assert part_count * part_size >= filesize


def test_validate_multipart_filesize():
    """Test validate_multipart_filesize function."""
    max_size = settings.S3_MULTIPART_UPLOAD_MAX_SIZE
    assert test_module.validate_multipart_filesize(max_size) is True
    assert test_module.validate_multipart_filesize(max_size + 1) is False
