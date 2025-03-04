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
