"""Tests for virtual lab API dependency."""

import re
from http import HTTPStatus
from uuid import UUID

import httpx
import pytest
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError

from app.config import settings
from app.dependencies import virtual_lab_api as test_module
from app.errors import ApiError, ApiErrorCode
from app.schemas.virtual_lab import ProjectVirtualLabMapping
from app.utils.virtual_lab import AdminVirtualLabClient

from tests.utils import PROJECT_ID, TOKEN_ADMIN, VIRTUAL_LAB_ID

VIRTUAL_LAB_API_TEST_URL = "https://virtual-lab-api.test"


@pytest.fixture
def virtual_lab_api_url(monkeypatch):
    monkeypatch.setattr(settings, "VIRTUAL_LAB_API_URL", VIRTUAL_LAB_API_TEST_URL)
    return VIRTUAL_LAB_API_TEST_URL


@pytest.fixture
def admin_bearer_credentials():
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=TOKEN_ADMIN)


def _virtual_lab_project_url(base_url: str, project_id: UUID | str = PROJECT_ID) -> str:
    return f"{base_url}/projects/{project_id}/virtual-lab"


def _mapping_response_json(
    project_id: UUID | str = PROJECT_ID,
    virtual_lab_id: UUID | str = VIRTUAL_LAB_ID,
) -> dict:
    return {
        "data": {
            "project_id": str(project_id),
            "virtual_lab_id": str(virtual_lab_id),
        },
    }


def test_get_admin_virtual_lab_client_uses_settings_and_token(
    user_context_admin,
    admin_bearer_credentials,
    virtual_lab_api_url,
):
    client = test_module.get_admin_virtual_lab_client(
        user_context_admin,
        admin_bearer_credentials,
    )

    assert isinstance(client, AdminVirtualLabClient)
    assert str(client._http_client.base_url) == virtual_lab_api_url
    assert client._http_client.headers["Authorization"] == f"Bearer {TOKEN_ADMIN}"


def test_get_admin_virtual_lab_client_ignores_user_context(
    admin_bearer_credentials,
    virtual_lab_api_url,
):
    client = test_module.get_admin_virtual_lab_client(
        None,
        admin_bearer_credentials,
    )

    assert isinstance(client, AdminVirtualLabClient)
    assert str(client._http_client.base_url) == virtual_lab_api_url


def test_get_virtual_lab_by_project_success(
    httpx_mock,
    user_context_admin,
    admin_bearer_credentials,
    virtual_lab_api_url,
):
    project_id = UUID(PROJECT_ID)
    virtual_lab_id = UUID(VIRTUAL_LAB_ID)
    httpx_mock.add_response(
        url=_virtual_lab_project_url(virtual_lab_api_url, project_id),
        json=_mapping_response_json(project_id, virtual_lab_id),
    )

    client = test_module.get_admin_virtual_lab_client(
        user_context_admin,
        admin_bearer_credentials,
    )
    mapping = client.get_virtual_lab_by_project(project_id)

    assert mapping == ProjectVirtualLabMapping(
        project_id=project_id,
        virtual_lab_id=virtual_lab_id,
    )
    request = httpx_mock.get_request()
    assert request.method == "GET"
    assert request.headers["Authorization"] == f"Bearer {TOKEN_ADMIN}"


def test_get_virtual_lab_by_project_http_status_error(
    httpx_mock,
    user_context_admin,
    admin_bearer_credentials,
    virtual_lab_api_url,
):
    project_id = UUID(PROJECT_ID)
    httpx_mock.add_response(
        url=_virtual_lab_project_url(virtual_lab_api_url, project_id),
        status_code=HTTPStatus.NOT_FOUND,
    )

    client = test_module.get_admin_virtual_lab_client(
        user_context_admin,
        admin_bearer_credentials,
    )

    with pytest.raises(ApiError) as exc_info:
        client.get_virtual_lab_by_project(project_id)

    assert exc_info.value.message == "HTTP status error 404"
    assert exc_info.value.error_code == ApiErrorCode.GENERIC_ERROR
    assert exc_info.value.http_status_code == HTTPStatus.INTERNAL_SERVER_ERROR


@pytest.mark.usefixtures("virtual_lab_api_url")
def test_get_virtual_lab_by_project_request_error(
    httpx_mock,
    user_context_admin,
    admin_bearer_credentials,
):
    project_id = UUID(PROJECT_ID)
    httpx_mock.add_exception(httpx.ConnectError("connection refused"))

    client = test_module.get_admin_virtual_lab_client(
        user_context_admin,
        admin_bearer_credentials,
    )

    with pytest.raises(ApiError) as exc_info:
        client.get_virtual_lab_by_project(project_id)

    assert exc_info.value.message == "HTTP request error"
    assert exc_info.value.error_code == ApiErrorCode.GENERIC_ERROR
    assert exc_info.value.http_status_code == HTTPStatus.INTERNAL_SERVER_ERROR


def test_get_virtual_lab_by_project_invalid_mapping_payload(
    httpx_mock,
    user_context_admin,
    admin_bearer_credentials,
    virtual_lab_api_url,
):
    project_id = UUID(PROJECT_ID)
    httpx_mock.add_response(
        url=_virtual_lab_project_url(virtual_lab_api_url, project_id),
        json={"data": {"project_id": "not-a-uuid", "virtual_lab_id": str(UUID(VIRTUAL_LAB_ID))}},
    )

    client = test_module.get_admin_virtual_lab_client(
        user_context_admin,
        admin_bearer_credentials,
    )

    with pytest.raises(ValidationError):
        client.get_virtual_lab_by_project(project_id)


def test_get_virtual_lab_by_project_missing_data_key(
    httpx_mock,
    user_context_admin,
    admin_bearer_credentials,
    virtual_lab_api_url,
):
    project_id = UUID(PROJECT_ID)
    httpx_mock.add_response(
        url=_virtual_lab_project_url(virtual_lab_api_url, project_id),
        json={"unexpected": "shape"},
    )

    client = test_module.get_admin_virtual_lab_client(
        user_context_admin,
        admin_bearer_credentials,
    )

    with pytest.raises(KeyError, match="data"):
        client.get_virtual_lab_by_project(project_id)


def test_admin_virtual_lab_client_direct_instantiation(
    httpx_mock,
    virtual_lab_api_url,
):
    project_id = UUID(PROJECT_ID)
    httpx_mock.add_response(
        url=re.compile(rf"{re.escape(virtual_lab_api_url)}/projects/.+/virtual-lab"),
        json=_mapping_response_json(project_id),
    )

    client = AdminVirtualLabClient(base_url=virtual_lab_api_url, token="direct-token")  # noqa: S106
    mapping = client.get_virtual_lab_by_project(project_id)

    assert mapping.project_id == project_id
    assert mapping.virtual_lab_id == UUID(VIRTUAL_LAB_ID)
    assert httpx_mock.get_request().headers["Authorization"] == "Bearer direct-token"
