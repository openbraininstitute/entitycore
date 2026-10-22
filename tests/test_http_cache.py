import pytest

import app.service.brain_atlas as brain_atlas_service
from app.db.model import BrainAtlasRegion
from app.utils.http_cache import CACHE_CONTROL, CachedJson, etag_matches, make_etag

from tests import test_brain_region, utils

HIERARCHY_ROUTE = "/brain-region-hierarchy"
ATLAS_ROUTE = "/brain-atlas"


@pytest.fixture
def regions_cache():
    read_json = brain_atlas_service._read_many_region_json
    read_json.cache_clear()
    yield read_json.cache
    read_json.cache_clear()


@pytest.fixture
def hierarchy_url(db, brain_region_hierarchy_id):
    utils.add_brain_region_hierarchy(db, test_brain_region.HIERARCHY, brain_region_hierarchy_id)
    return f"{HIERARCHY_ROUTE}/{brain_region_hierarchy_id}/hierarchy"


@pytest.fixture
def add_region(db, brain_atlas_id, brain_region_id, user_id):
    def _add_region(*, authorized_public=True):
        return utils.add_db(
            db,
            BrainAtlasRegion(
                volume=1.0,
                is_leaf_region=True,
                brain_region_id=brain_region_id,
                brain_atlas_id=brain_atlas_id,
                authorized_project_id=utils.PROJECT_ID,
                authorized_public=authorized_public,
                created_by_id=user_id,
                updated_by_id=user_id,
            ),
        )

    return _add_region


@pytest.fixture
def regions_url(brain_atlas_id):
    return f"{ATLAS_ROUTE}/{brain_atlas_id}/regions"


def _ids(response):
    return {item["id"] for item in response.json()["data"]}


def test_make_etag():
    etag = make_etag(b"content")
    assert etag.startswith('W/"')
    assert etag.endswith('"')
    assert etag == make_etag(b"content")
    assert etag != make_etag(b"other content")


@pytest.mark.parametrize(
    ("if_none_match", "expected"),
    [
        (None, False),
        ("", False),
        ('W/"abc"', True),
        ('"abc"', True),
        ('W/"other"', False),
        ('W/"other", W/"abc"', True),
        ('W/"other",W/"abc"', True),
        ("*", True),
    ],
)
def test_etag_matches(if_none_match, expected):
    assert etag_matches(if_none_match, 'W/"abc"') is expected


def test_cached_json_from_content():
    cached = CachedJson.from_content(b"{}")
    assert cached.content == b"{}"
    assert cached.etag == make_etag(b"{}")
    assert cached.size() == 2


def test_hierarchy_etag(client, hierarchy_url):
    response = utils.assert_request(client.get, url=hierarchy_url)
    etag = response.headers["etag"]
    assert etag.startswith('W/"')
    assert response.headers["cache-control"] == CACHE_CONTROL

    response = client.get(hierarchy_url, headers={"If-None-Match": etag})
    assert response.status_code == 304
    assert response.content == b""
    assert response.headers["etag"] == etag
    assert response.headers["cache-control"] == CACHE_CONTROL
    assert "content-encoding" not in response.headers

    response = client.get(hierarchy_url, headers={"If-None-Match": 'W/"stale"'})
    assert response.status_code == 200
    assert response.headers["etag"] == etag
    assert response.json()["acronym"] == "root"


@pytest.mark.usefixtures("regions_cache")
def test_regions_etag(client, add_region, regions_url):
    region = add_region()

    response = utils.assert_request(client.get, url=regions_url)
    etag = response.headers["etag"]
    assert response.headers["cache-control"] == CACHE_CONTROL
    assert _ids(response) == {str(region.id)}

    response = client.get(regions_url, headers={"If-None-Match": etag})
    assert response.status_code == 304
    assert response.content == b""
    assert response.headers["etag"] == etag

    response = client.get(regions_url, headers={"If-None-Match": 'W/"stale"'})
    assert response.status_code == 200
    assert _ids(response) == {str(region.id)}


def test_regions_cached_until_ttl(client, add_region, regions_url, regions_cache):
    region_1 = add_region()
    response = utils.assert_request(client.get, url=regions_url)
    etag = response.headers["etag"]

    region_2 = add_region()
    regions_cache.expire(time=regions_cache.timer() + regions_cache.ttl - 1)
    response = utils.assert_request(client.get, url=regions_url)
    assert _ids(response) == {str(region_1.id)}
    assert response.headers["etag"] == etag

    regions_cache.expire(time=regions_cache.timer() + regions_cache.ttl)
    response = utils.assert_request(client.get, url=regions_url)
    assert _ids(response) == {str(region_1.id), str(region_2.id)}
    assert response.headers["etag"] != etag


def test_regions_cache_key(client, add_region, regions_url, regions_cache):
    add_region()
    add_region()

    response = utils.assert_request(client.get, url=regions_url)
    assert len(response.json()["data"]) == 2

    response = utils.assert_request(client.get, url=regions_url, params={"page_size": 1})
    assert len(response.json()["data"]) == 1

    assert len(regions_cache) == 2


def test_regions_cache_shared_without_private_regions(
    client, client_user_2, client_no_project, add_region, regions_url, regions_cache
):
    region = add_region(authorized_public=True)

    etags = set()
    for any_client in (client, client_user_2, client_no_project):
        response = utils.assert_request(any_client.get, url=regions_url)
        assert _ids(response) == {str(region.id)}
        etags.add(response.headers["etag"])

    assert len(etags) == 1
    assert len(regions_cache) == 1


def test_regions_cache_per_project_with_private_regions(
    client, client_user_2, client_no_project, add_region, regions_url, regions_cache
):
    public_region = add_region(authorized_public=True)
    private_region = add_region(authorized_public=False)

    response = utils.assert_request(client.get, url=regions_url)
    assert _ids(response) == {str(public_region.id), str(private_region.id)}
    etag = response.headers["etag"]

    for other_client in (client_user_2, client_no_project):
        response = utils.assert_request(other_client.get, url=regions_url)
        assert _ids(response) == {str(public_region.id)}

        # the ETag of the private regions doesn't match the content visible to other projects
        response = other_client.get(regions_url, headers={"If-None-Match": etag})
        assert response.status_code == 200
        assert _ids(response) == {str(public_region.id)}

    assert len(regions_cache) == 2


@pytest.mark.usefixtures("regions_cache")
def test_regions_compressed_with_etag(client, add_region, regions_url):
    for _ in range(5):
        add_region()

    response = utils.assert_request(
        client.get, url=regions_url, headers={"Accept-Encoding": "gzip"}
    )
    assert response.headers["content-encoding"] == "gzip"
    etag = response.headers["etag"]

    response = client.get(regions_url, headers={"Accept-Encoding": "gzip", "If-None-Match": etag})
    assert response.status_code == 304
    assert "content-encoding" not in response.headers
