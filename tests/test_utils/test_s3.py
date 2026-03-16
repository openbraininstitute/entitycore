import io
import math
from pathlib import Path
from unittest.mock import Mock

import botocore.exceptions
import pytest
from fastapi import HTTPException

from app.config import settings
from app.db.types import EntityType
from app.utils import s3 as test_module

from tests.utils import PROJECT_ID, VIRTUAL_LAB_ID

pytestmark = pytest.mark.usefixtures("_create_buckets")


def _fail_on_second_call(original, error_msg):
    """Return a Mock that delegates the first call and raises on the second."""

    def side_effect(**kwargs):
        if mock.call_count > 1:
            raise RuntimeError(error_msg)
        return original(**kwargs)

    mock = Mock(side_effect=side_effect)
    return mock


def _upload(s3, bucket, key, data=b"content"):
    s3.upload_fileobj(io.BytesIO(data), Bucket=bucket, Key=key)


def _exists(s3, bucket, key):
    try:
        s3.head_object(Bucket=bucket, Key=key)
    except botocore.exceptions.ClientError:
        return False
    return True


def _read(s3, bucket, key):
    return s3.get_object(Bucket=bucket, Key=key)["Body"].read()


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


def test_ensure_directory_prefix():
    assert test_module.ensure_directory_prefix("foo") == "foo/"
    assert test_module.ensure_directory_prefix("foo/") == "foo/"
    assert test_module.ensure_directory_prefix("a/b/c") == "a/b/c/"


def test_convert_s3_path_visibility_private_to_public():
    path = "private/vlab/proj/assets/morph/1/file.asc"
    result = test_module.convert_s3_path_visibility(path, public=True)
    assert result == "public/vlab/proj/assets/morph/1/file.asc"


def test_convert_s3_path_visibility_public_to_private():
    path = "public/vlab/proj/assets/morph/1/file.asc"
    result = test_module.convert_s3_path_visibility(path, public=False)
    assert result == "private/vlab/proj/assets/morph/1/file.asc"


def test_convert_s3_path_visibility_wrong_prefix():
    with pytest.raises(ValueError, match="must start with"):
        test_module.convert_s3_path_visibility("public/file.txt", public=True)
    with pytest.raises(ValueError, match="must start with"):
        test_module.convert_s3_path_visibility("private/file.txt", public=False)


def test_copy_file_simple(s3, s3_internal_bucket):
    bucket = s3_internal_bucket
    _upload(s3, bucket, "src/file.txt", b"hello")

    test_module.copy_file(
        s3,
        src_bucket_name=bucket,
        dst_bucket_name=bucket,
        src_key="src/file.txt",
        dst_key="dst/file.txt",
        size=5,
    )

    assert _read(s3, bucket, "dst/file.txt") == b"hello"
    assert _exists(s3, bucket, "src/file.txt")


def test_copy_file_multipart(s3, s3_internal_bucket, monkeypatch):
    bucket = s3_internal_bucket
    part_size = 5 * 1024 * 1024  # cannot be smaller than the minimum allowed object size
    data = b"x" * (part_size + 100)
    _upload(s3, bucket, "src/big.bin", data)

    monkeypatch.setattr(settings, "S3_MULTIPART_UPLOAD_MAX_PART_SIZE", part_size)

    test_module.copy_file(
        s3,
        src_bucket_name=bucket,
        dst_bucket_name=bucket,
        src_key="src/big.bin",
        dst_key="dst/big.bin",
        size=len(data),
    )

    assert _read(s3, bucket, "dst/big.bin") == data


def test_copy_file_multipart_abort_success(s3, s3_internal_bucket, monkeypatch):
    """The original exception is re-raised when abort_multipart_upload succeeds."""
    bucket = s3_internal_bucket
    part_size = 5 * 1024 * 1024
    data = b"x" * (part_size + 100)
    _upload(s3, bucket, "src/fail.bin", data)

    error_msg = "upload_part_copy failed"
    upload_part_copy_mock = _fail_on_second_call(s3.upload_part_copy, error_msg=error_msg)

    monkeypatch.setattr(settings, "S3_MULTIPART_UPLOAD_MAX_PART_SIZE", part_size)
    monkeypatch.setattr(s3, "upload_part_copy", upload_part_copy_mock)

    with pytest.raises(RuntimeError, match=error_msg):
        test_module.copy_file(
            s3,
            src_bucket_name=bucket,
            dst_bucket_name=bucket,
            src_key="src/fail.bin",
            dst_key="dst/fail.bin",
            size=len(data),
        )
    assert upload_part_copy_mock.call_count == 2


def test_copy_file_multipart_abort_failure(s3, s3_internal_bucket, monkeypatch):
    """The original exception is re-raised even when abort_multipart_upload fails."""
    bucket = s3_internal_bucket
    part_size = 5 * 1024 * 1024
    data = b"x" * (part_size + 100)
    _upload(s3, bucket, "src/fail.bin", data)

    error_msg = "upload_part_copy failed"
    upload_part_copy_mock = _fail_on_second_call(s3.upload_part_copy, error_msg=error_msg)
    abort_multipart_upload_mock = Mock(side_effect=RuntimeError("abort failed"))

    monkeypatch.setattr(settings, "S3_MULTIPART_UPLOAD_MAX_PART_SIZE", part_size)
    monkeypatch.setattr(s3, "upload_part_copy", upload_part_copy_mock)
    monkeypatch.setattr(s3, "abort_multipart_upload", abort_multipart_upload_mock)

    with pytest.raises(RuntimeError, match=error_msg):
        test_module.copy_file(
            s3,
            src_bucket_name=bucket,
            dst_bucket_name=bucket,
            src_key="src/fail.bin",
            dst_key="dst/fail.bin",
            size=len(data),
        )
    assert upload_part_copy_mock.call_count == 2
    assert abort_multipart_upload_mock.call_count == 1


def test_move_file(s3, s3_internal_bucket):
    bucket = s3_internal_bucket
    _upload(s3, bucket, "src/move.txt", b"move me")

    test_module.move_file(
        s3,
        src_bucket_name=bucket,
        dst_bucket_name=bucket,
        src_key="src/move.txt",
        dst_key="dst/move.txt",
        size=7,
        dry_run=False,
    )

    assert _read(s3, bucket, "dst/move.txt") == b"move me"
    assert not _exists(s3, bucket, "src/move.txt")


def test_move_file_dry_run(s3, s3_internal_bucket):
    bucket = s3_internal_bucket
    _upload(s3, bucket, "src/dry.txt", b"stay")

    test_module.move_file(
        s3,
        src_bucket_name=bucket,
        dst_bucket_name=bucket,
        src_key="src/dry.txt",
        dst_key="dst/dry.txt",
        size=4,
        dry_run=True,
    )

    assert _exists(s3, bucket, "src/dry.txt")
    assert not _exists(s3, bucket, "dst/dry.txt")


def test_move_file_same_src_dst(s3, s3_internal_bucket):
    bucket = s3_internal_bucket
    with pytest.raises(ValueError, match="Source and destination cannot be the same"):
        test_module.move_file(
            s3,
            src_bucket_name=bucket,
            dst_bucket_name=bucket,
            src_key="same.txt",
            dst_key="same.txt",
            size=1,
            dry_run=False,
        )


def test_move_file_already_moved(s3, s3_internal_bucket):
    bucket = s3_internal_bucket
    _upload(s3, bucket, "dst/already.txt", b"already there")

    test_module.move_file(
        s3,
        src_bucket_name=bucket,
        dst_bucket_name=bucket,
        src_key="src/already.txt",
        dst_key="dst/already.txt",
        size=13,
        dry_run=False,
    )

    assert _read(s3, bucket, "dst/already.txt") == b"already there"


def test_move_file_source_missing_dest_missing(s3, s3_internal_bucket):
    bucket = s3_internal_bucket
    with pytest.raises(HTTPException, match="500"):
        test_module.move_file(
            s3,
            src_bucket_name=bucket,
            dst_bucket_name=bucket,
            src_key="src/gone.txt",
            dst_key="dst/gone.txt",
            size=1,
            dry_run=False,
        )


def test_move_directory(s3, s3_internal_bucket):
    bucket = s3_internal_bucket
    _upload(s3, bucket, "srcdir/a.txt", b"aaa")
    _upload(s3, bucket, "srcdir/b.txt", b"bb")

    result = test_module.move_directory(
        s3,
        src_bucket_name=bucket,
        dst_bucket_name=bucket,
        src_key="srcdir",
        dst_key="dstdir",
        dry_run=False,
    )

    assert result.total_file_count == 2
    assert result.total_file_size == 5
    assert _read(s3, bucket, "dstdir/a.txt") == b"aaa"
    assert _read(s3, bucket, "dstdir/b.txt") == b"bb"
    assert not _exists(s3, bucket, "srcdir/a.txt")
    assert not _exists(s3, bucket, "srcdir/b.txt")


def test_move_directory_dry_run(s3, s3_internal_bucket):
    bucket = s3_internal_bucket
    _upload(s3, bucket, "srcdir2/c.txt", b"ccc")

    result = test_module.move_directory(
        s3,
        src_bucket_name=bucket,
        dst_bucket_name=bucket,
        src_key="srcdir2",
        dst_key="dstdir2",
        dry_run=True,
    )

    assert result.total_file_count == 1
    assert result.total_file_size == 3
    assert _exists(s3, bucket, "srcdir2/c.txt")
    assert not _exists(s3, bucket, "dstdir2/c.txt")
