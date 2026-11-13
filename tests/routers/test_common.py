import types

import pytest

from app.routers import common as test_module
from app.routers.common import UserOperation


def _make_service():
    def read_many():
        pass

    def read_one(id_: str):
        pass

    def create_one():
        pass

    def update_one(id_: str):
        pass

    def delete_one(id_: str):
        pass

    return types.SimpleNamespace(
        read_many=read_many,
        read_one=read_one,
        create_one=create_one,
        update_one=update_one,
        delete_one=delete_one,
    )


def _routes(router):
    return [(next(iter(route.methods)), route.path, route.name) for route in router.routes]


def test_create_user_router_all_operations():
    router = test_module.create_user_router(route="resource", service=_make_service())

    assert _routes(router) == [
        ("GET", "/resource", "read_many"),
        ("GET", "/resource/{id_}", "read_one"),
        ("POST", "/resource", "create_one"),
        ("PATCH", "/resource/{id_}", "update_one"),
        ("DELETE", "/resource/{id_}", "delete_one"),
    ]
    assert router.tags == ["resource"]


def test_create_user_router_operations_subset():
    router = test_module.create_user_router(
        route="resource",
        service=_make_service(),
        # registered in the order of UserOperation
        operations=[UserOperation.read_one, UserOperation.read_many],
    )

    assert _routes(router) == [
        ("GET", "/resource", "read_many"),
        ("GET", "/resource/{id_}", "read_one"),
    ]


def test_create_user_router_before_and_after_routes():
    def before(router):
        router.get("/before")(lambda: None)

    def after(router):
        router.get("/after")(lambda: None)

    router = test_module.create_user_router(
        route="resource",
        service=_make_service(),
        operations={UserOperation.read_one},
        before_routes=[before],
        after_routes=[after],
    )

    assert [path for _, path, _ in _routes(router)] == [
        "/resource/before",
        "/resource/{id_}",
        "/resource/after",
    ]


def test_create_user_router_missing_service_function():
    service = _make_service()
    del service.create_one

    with pytest.raises(AttributeError, match="create_one"):
        test_module.create_user_router(route="resource", service=service)

    # not needed when the operation isn't registered
    router = test_module.create_user_router(
        route="resource",
        service=service,
        operations=set(UserOperation) - {UserOperation.create_one},
    )
    assert "create_one" not in {name for _, _, name in _routes(router)}


def test_user_operation_routes_complete():
    assert set(test_module.USER_OPERATION_ROUTES) == set(UserOperation)
