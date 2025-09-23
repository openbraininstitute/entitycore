import json
import re
from collections import defaultdict

import pytest

from app.application import app
from app.utils.routers import EntityRoute, GlobalRoute

REGEX_PATTERN = r"^\/(?:admin\/)?{route}(?:\/{{.+}})?$"


@pytest.fixture(scope="module")
def entity_routes():
    return [str(s) for s in EntityRoute]


@pytest.fixture(scope="module")
def global_routes():
    return [str(s) for s in GlobalRoute]


def _group_routes(app, routes):
    per_route_methods = defaultdict(list)

    for route_name in routes:
        pattern = re.compile(REGEX_PATTERN.format(route=route_name))
        for route in app.routes:
            if pattern.match(route.path):
                per_route_methods[route_name].append(route)

    return dict(per_route_methods)


@pytest.fixture(scope="module")
def entity_route_paths(entity_routes):
    return _group_routes(app, entity_routes)


@pytest.fixture(scope="module")
def global_route_paths(global_routes):
    return _group_routes(app, global_routes)


def _assert_routes(route_paths, expected_method_names, skip):
    missing = {}

    for route, paths in route_paths.items():
        if route in skip:
            continue

        method_names = {p.name for p in paths}

        if missing_method_names := [
            name for name in expected_method_names if name not in method_names
        ]:
            missing[route] = missing_method_names

    assert not missing, f"Missing route methods: {json.dumps(missing, indent=2)}"


def test_entity_route_methods(entity_route_paths):
    expected_method_names = {
        "read_one",
        "read_many",
        "create_one",
        "update_one",
        "admin_read_one",
        "admin_update_one",
    }

    # the following must be clarified:
    # why is ion-channel is an entity?
    # why is em-dense-recostruction-dataset an entity?
    # why is external-url an entity?
    skip = {
        "brain-atlas",
        "cell-composition",
        "ion-channel",
        "em-dense-reconstruction-dataset",
        "external-url",
    }

    _assert_routes(entity_route_paths, expected_method_names, skip)


def test_global_route_methods(global_route_paths):
    expected_method_names = {
        "read_one",
        "read_many",
        "create_one",
        "update_one",
        "admin_read_one",
        "admin_update_one",
    }

    skip = {"brain-region-hierarchy"}

    _assert_routes(global_route_paths, expected_method_names, skip)
