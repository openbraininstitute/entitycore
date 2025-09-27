import json
import re
from collections import defaultdict
from dataclasses import dataclass

import pytest

from app.application import app
from app.utils.routers import ActivityRoute, EntityRoute, GlobalRoute, ResourceRoute


@dataclass
class Route:
    name: str
    path: str
    method: str


REGEX_PATTERN = re.compile(r"^/(?P<route>(?!\{)[a-z0-9-]+)(?=/|$)")


@pytest.fixture(scope="module")
def routes():  # noqa: C901
    def _route(is_admin, route):
        name = route.name

        if is_admin and not route.name.startswith("admin"):
            name = f"admin_{name}"

        if "derived-from" in route.path and not name.endswith("derivation"):
            name = f"{name}_derivation"

        return Route(
            name=name,
            path=route.path.replace("{entity_route}", route_name).replace("{route}", route_name),  # noqa: RUF027
            method=next(iter(route.methods)),
        )

    groups = defaultdict(list)
    for route in app.routes:
        path = route.path

        if path in {
            "/docs",
            "/docs/oauth2-redirect",
            "/redoc",
            "/health",
            "/version",
            "/error",
            "/openapi.json",
            "/",
        }:
            continue

        is_admin = False
        if path.startswith("/admin"):
            is_admin = True
            path = path.replace("/admin", "")

        # expand all entity route paths
        if "{entity_route}" in path:
            for route_name in EntityRoute:
                groups[str(route_name)].append(_route(is_admin, route))
            continue

        # expand all resource route paths
        if "{route}" in path:  # noqa: RUF027
            for route_name in ResourceRoute:
                groups[str(route_name)].append(_route(is_admin, route))
            continue

        match = REGEX_PATTERN.match(path)
        assert match, route
        groups[match["route"]].append(_route(is_admin, route))

    return {k: sorted(v, key=lambda r: r.name) for k, v in groups.items()}


@pytest.fixture(scope="module")
def entity_routes(routes):
    return {str(k): routes[k] for k in EntityRoute}


@pytest.fixture(scope="module")
def global_routes(routes):
    return {str(k): routes[k] for k in GlobalRoute}


@pytest.fixture(scope="module")
def activity_routes(routes):
    return {str(k): routes[k] for k in ActivityRoute}


def _assert_routes(route_paths, expected_method_names, skip):
    missing = {}

    for name, routes in route_paths.items():
        if name in skip:
            continue

        method_names = {route.name for route in routes}

        if missing_method_names := [
            method_name for method_name in expected_method_names if method_name not in method_names
        ]:
            missing[name] = missing_method_names

    assert not missing, f"Missing route methods: {json.dumps(missing, indent=2)}"


def test_entity_route_methods(entity_routes):
    expected_method_names = {
        "read_one",
        "read_many",
        "create_one",
        "update_one",
        "delete_one",
        "admin_read_one",
        "admin_update_one",
        "admin_delete_one",
        "admin_delete_entity_asset",
        "admin_get_entity_asset",
        "admin_get_entity_assets",
        "delete_entity_asset",
        "download_entity_asset",
        "entity_asset_directory_list",
        "entity_asset_directory_upload",
        "get_entity_asset",
        "get_entity_assets",
        "read_many_derivation",
        "register_entity_asset",
        "upload_entity_asset",
    }

    # the following must be clarified:
    # why is ion-channel is an entity?
    # why is em-dense-recostruction-dataset an entity?
    # why is external-url an entity?
    skip = {
        "brain-atlas",
        "brain-atlas-region",
        "cell-composition",
        "ion-channel",
        "em-dense-reconstruction-dataset",
        "external-url",
        "scientific-artifact",  # no router, remove from EntityRoute?
        "me-type-density",
        "analysis-software-source-code",  # no router, remove from EntityRoute?
        "electrical-recording",  # no router, remove from EntityRoute?
    }

    _assert_routes(entity_routes, expected_method_names, skip)


def test_global_route_methods(global_routes):
    expected_method_names = {
        "read_one",
        "read_many",
        "create_one",
        "update_one",
        "delete_one",
        "admin_read_one",
        "admin_update_one",
        "admin_delete_one",
    }

    skip = {"brain-region-hierarchy", "ion"}

    _assert_routes(global_routes, expected_method_names, skip)

'''
def test_activity_route_methods(activity_routes):
    expected_method_names = [
        "read_one",
        "read_many,create_one",
        "update_one",
        "delete_one",
        "admin_read_one",
        "admin_update_one",
    ]
    skip = set()
    _assert_routes(activity_routes, expected_method_names, skip)
'''
