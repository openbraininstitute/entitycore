"""Tests for the auth dependencies, with the real KeyCloak check and a mocked KeyCloak."""

import time
from contextlib import asynccontextmanager
from http import HTTPStatus
from uuid import UUID

import httpx2
import jwt
import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from app.application import api_error_handler
from app.config import settings
from app.dependencies import auth as test_module
from app.dependencies.auth import AdminContextDep, UserContextDep
from app.errors import ApiError, AuthErrorReason
from app.middleware import RequestContextMiddleware
from app.schemas.auth import UserContext, UserProfile

from tests.utils import (
    PROJECT_ID,
    UNRELATED_PROJECT_ID,
    UNRELATED_VIRTUAL_LAB_ID,
    USER_SUB_ID_1,
    VIRTUAL_LAB_ID,
)

TOKEN = "a-token"  # ruff:ignore[hardcoded-password-string]
AUTH_HEADER = {"Authorization": f"Bearer {TOKEN}"}
ADMIN_GROUP = f"/service/{settings.APP_NAME}/admin"
PROJECT_GROUP = f"/proj/{VIRTUAL_LAB_ID}/{PROJECT_ID}/member"
NON_MEMBER_HEADERS = {
    "virtual-lab-id": UNRELATED_VIRTUAL_LAB_ID,
    "project-id": UNRELATED_PROJECT_ID,
}
MEMBER_HEADERS = {"virtual-lab-id": VIRTUAL_LAB_ID, "project-id": PROJECT_ID}


def _context_json(user_context: UserContext) -> dict:
    return {
        "virtual_lab_id": user_context.virtual_lab_id and str(user_context.virtual_lab_id),
        "project_id": user_context.project_id and str(user_context.project_id),
        "is_authorized": user_context.is_authorized,
        "is_service_admin": user_context.is_service_admin,
    }


def _make_test_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        with httpx2.Client() as http_client:
            yield {"http_client": http_client}

    test_app = FastAPI(lifespan=lifespan)
    test_app.add_middleware(RequestContextMiddleware)
    test_app.add_exception_handler(ApiError, api_error_handler)  # pyright: ignore[reportArgumentType]

    # routers wired as in app.routers: user routes depend on user_verified at the router level,
    # admin routes on user_with_service_admin_role
    user_router = APIRouter()
    admin_router = APIRouter(prefix="/admin")

    @user_router.get("/user")
    def user_endpoint(user_context: UserContextDep):
        return _context_json(user_context)

    @user_router.get("/user-admin-only")
    def user_admin_only_endpoint(user_context: AdminContextDep):
        """User route restricted to admins, like the create of the global resources."""
        return _context_json(user_context)

    @admin_router.get("/resource")
    def admin_endpoint(user_context: AdminContextDep):
        return _context_json(user_context)

    test_app.include_router(user_router, dependencies=[Depends(test_module.user_verified)])
    test_app.include_router(
        admin_router, dependencies=[Depends(test_module.user_with_service_admin_role)]
    )
    return test_app


@pytest.fixture(autouse=True)  # ruff: ignore[pytest-fixture-autouse]
def _clear_auth_cache():
    test_module._check_user_info.cache_clear()
    yield
    test_module._check_user_info.cache_clear()


@pytest.fixture
def test_client():
    with TestClient(_make_test_app()) as client:
        yield client


@pytest.fixture
def mock_keycloak(httpx2_mock):
    def _mock_keycloak(groups, status_code=HTTPStatus.OK):
        return httpx2_mock.get(test_module.KEYCLOAK_GROUPS_URL).respond(
            status_code,
            json={
                "sub": USER_SUB_ID_1,
                "preferred_username": "user",
                "groups": groups,
            },
        )

    return _mock_keycloak


def _get(client, url, headers=None, expected_status_code=HTTPStatus.OK):
    response = client.get(url, headers=AUTH_HEADER | (headers or {}))
    assert response.status_code == expected_status_code, response.json()
    return response.json()


def test_admin_route_admin_not_member(test_client, mock_keycloak):
    mock_keycloak([ADMIN_GROUP])

    data = _get(test_client, "/admin/resource", headers=NON_MEMBER_HEADERS)
    assert data == {
        "virtual_lab_id": UNRELATED_VIRTUAL_LAB_ID,
        "project_id": UNRELATED_PROJECT_ID,
        "is_authorized": True,
        "is_service_admin": True,
    }

    # only the project-id: the virtual lab can't be derived from the groups
    data = _get(test_client, "/admin/resource", headers={"project-id": UNRELATED_PROJECT_ID})
    assert data["project_id"] == UNRELATED_PROJECT_ID
    assert data["virtual_lab_id"] is None


def test_admin_route_admin_member(test_client, mock_keycloak):
    mock_keycloak([ADMIN_GROUP, PROJECT_GROUP])

    data = _get(test_client, "/admin/resource", headers={"project-id": PROJECT_ID})
    assert data["project_id"] == PROJECT_ID
    assert data["virtual_lab_id"] == VIRTUAL_LAB_ID

    data = _get(test_client, "/admin/resource")
    assert data["project_id"] is None
    assert data["virtual_lab_id"] is None


def test_admin_route_not_admin(test_client, mock_keycloak):
    mock_keycloak([PROJECT_GROUP])

    data = _get(
        test_client,
        "/admin/resource",
        headers=MEMBER_HEADERS,
        expected_status_code=HTTPStatus.FORBIDDEN,
    )
    assert data["message"] == AuthErrorReason.ADMIN_REQUIRED

    data = _get(
        test_client,
        "/admin/resource",
        headers=NON_MEMBER_HEADERS,
        expected_status_code=HTTPStatus.FORBIDDEN,
    )
    assert data["message"] == AuthErrorReason.NOT_AUTHORIZED_PROJECT


@pytest.mark.parametrize("url", ["/user", "/user-admin-only"])
def test_user_routes_admin_not_member(test_client, mock_keycloak, url):
    """Service admins have no special privilege on the user routes."""
    mock_keycloak([ADMIN_GROUP])

    data = _get(
        test_client, url, headers=NON_MEMBER_HEADERS, expected_status_code=HTTPStatus.FORBIDDEN
    )
    assert data["message"] == AuthErrorReason.NOT_AUTHORIZED_PROJECT

    data = _get(
        test_client,
        url,
        headers={"project-id": UNRELATED_PROJECT_ID},
        expected_status_code=HTTPStatus.FORBIDDEN,
    )
    assert data["message"] == AuthErrorReason.NOT_AUTHORIZED_PROJECT


@pytest.mark.parametrize("url", ["/user", "/user-admin-only"])
def test_user_routes_admin_member(test_client, mock_keycloak, url):
    mock_keycloak([ADMIN_GROUP, PROJECT_GROUP])

    data = _get(test_client, url, headers=MEMBER_HEADERS)
    assert data["project_id"] == PROJECT_ID
    assert data["virtual_lab_id"] == VIRTUAL_LAB_ID


def test_user_route_admin_only_not_admin(test_client, mock_keycloak):
    mock_keycloak([PROJECT_GROUP])

    data = _get(
        test_client,
        "/user-admin-only",
        headers=MEMBER_HEADERS,
        expected_status_code=HTTPStatus.FORBIDDEN,
    )
    assert data["message"] == AuthErrorReason.ADMIN_REQUIRED


def test_admin_route_keycloak_not_authenticated(test_client, mock_keycloak):
    mock_keycloak([ADMIN_GROUP], status_code=HTTPStatus.UNAUTHORIZED)

    data = _get(
        test_client,
        "/admin/resource",
        headers=NON_MEMBER_HEADERS,
        expected_status_code=HTTPStatus.UNAUTHORIZED,
    )
    assert data["message"] == AuthErrorReason.NOT_AUTHENTICATED_USER


def test_admin_route_expired_token(test_client, httpx2_mock):
    expired_token = jwt.encode(
        {"sub": USER_SUB_ID_1, "preferred_username": "user", "exp": time.time() - 10},
        key="a-secret-key-long-enough-for-hs256",
        algorithm="HS256",
    )

    response = test_client.get(
        "/admin/resource",
        headers={"Authorization": f"Bearer {expired_token}"} | NON_MEMBER_HEADERS,
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()["message"] == AuthErrorReason.AUTH_TOKEN_EXPIRED
    # KeyCloak isn't called for expired tokens
    assert not httpx2_mock.calls


def test_admin_route_missing_token(test_client):
    response = test_client.get("/admin/resource", headers=NON_MEMBER_HEADERS)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()["message"] == AuthErrorReason.AUTH_TOKEN_MISSING


def _user_context(*, is_authorized, auth_error_reason, expiration):
    return UserContext(
        profile=UserProfile(subject=UUID(USER_SUB_ID_1), name="User"),
        expiration=expiration,
        is_authorized=is_authorized,
        is_service_admin=True,
        auth_error_reason=auth_error_reason,
    )


@pytest.mark.parametrize(
    ("is_authorized", "auth_error_reason"),
    [
        (True, None),
        # accepted on the admin routes, so it must not outlive the token
        (False, AuthErrorReason.NOT_AUTHORIZED_PROJECT),
    ],
)
def test_get_cache_ttu_token_expiration(is_authorized, auth_error_reason):
    now = 1000.0
    token_expiration = now + 10
    value = _user_context(
        is_authorized=is_authorized,
        auth_error_reason=auth_error_reason,
        expiration=token_expiration,
    )
    assert test_module._get_cache_ttu(None, value, now) == token_expiration


def test_get_cache_ttu_expired_token():
    now = 1000.0
    value = _user_context(
        is_authorized=False,
        auth_error_reason=AuthErrorReason.AUTH_TOKEN_EXPIRED,
        expiration=now - 10,
    )
    assert test_module._get_cache_ttu(None, value, now) == now + settings.AUTH_CACHE_MAX_TTL


def test_app_routes_admin_not_member(db, session_client, mock_keycloak):  # ruff:ignore[unused-function-argument]
    """Check the wiring of the dependencies in the app, with an admin not member of the project."""
    mock_keycloak([ADMIN_GROUP])

    data = _get(session_client, "/admin/cell-morphology", headers=NON_MEMBER_HEADERS)
    assert data["data"] == []

    data = _get(
        session_client,
        "/cell-morphology",
        headers=NON_MEMBER_HEADERS,
        expected_status_code=HTTPStatus.FORBIDDEN,
    )
    assert data["message"] == AuthErrorReason.NOT_AUTHORIZED_PROJECT

    # user route restricted to admins
    response = session_client.post(
        "/license",
        headers=AUTH_HEADER | NON_MEMBER_HEADERS,
        json={"name": "license", "description": "description", "label": "label"},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN, response.json()
    assert response.json()["message"] == AuthErrorReason.NOT_AUTHORIZED_PROJECT
