from pathlib import Path

from app.db.types import EntityType
from app.utils import s3 as test_module

from tests.utils import PROJECT_ID, VIRTUAL_LAB_ID


def test_build_s3_path_private():
    entity_id = 123456
    result = test_module.build_s3_path(
        vlab_id=VIRTUAL_LAB_ID,
        proj_id=PROJECT_ID,
        entity_type=EntityType.reconstruction_morphology,
        entity_id=entity_id,
        filename="a/b/c.txt",
        is_public=False,
    )
    assert result == (
        f"private/{VIRTUAL_LAB_ID}/{PROJECT_ID}/"
        f"assets/reconstruction_morphology/{entity_id}/a/b/c.txt"
    )


def test_build_s3_path_public():
    entity_id = 123456
    result = test_module.build_s3_path(
        vlab_id=VIRTUAL_LAB_ID,
        proj_id=PROJECT_ID,
        entity_type=EntityType.reconstruction_morphology,
        entity_id=entity_id,
        filename="a/b/c.txt",
        is_public=True,
    )
    assert result == (
        f"public/{VIRTUAL_LAB_ID}/{PROJECT_ID}/"
        f"assets/reconstruction_morphology/{entity_id}/a/b/c.txt"
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
