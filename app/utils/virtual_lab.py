import uuid
from http import HTTPStatus
from typing import Protocol
from uuid import UUID

import httpx2

from app.config import settings
from app.errors import ApiError, ApiErrorCode
from app.schemas.auth import UserContext
from app.schemas.virtual_lab import ProjectVirtualLabMapping
from app.utils.http import make_http_request


class AdminVirtualLabClientProtocol(Protocol):
    """Interface used by the service layer to resolve a virtual lab from a project."""

    def get_virtual_lab_by_project(self, project_id: UUID) -> ProjectVirtualLabMapping: ...

    def close(self) -> None: ...


class VirtualLabClient:
    """Client for virtual lab api user endpoints."""

    def __init__(self, base_url: str, token: str) -> None:
        """Instantiate client for virtual lab api."""
        self._http_client = httpx2.Client(
            base_url=base_url, headers={"Authorization": f"Bearer {token}"}
        )

    def close(self) -> None:
        """Close the underlying HTTP client and release its resources."""
        self._http_client.close()


class AdminVirtualLabClient(VirtualLabClient):
    def get_virtual_lab_by_project(self, project_id: UUID) -> ProjectVirtualLabMapping:
        response = make_http_request(
            url=f"/virtual-labs/projects/{project_id}/virtual-lab",
            http_client=self._http_client,
            method="GET",
        )
        return ProjectVirtualLabMapping.model_validate(response.json()["data"])


class DisabledAuthVirtualLabClient:
    """No-op admin client used when ``APP_DISABLE_AUTH`` is enabled.

    The virtual lab API is neither reachable nor authenticated in local dev, so the virtual lab
    id is resolved via ``resolve_virtual_lab_id`` instead. This client exists only to satisfy the
    dependency and raises if it is ever actually used.
    """

    def get_virtual_lab_by_project(self, project_id: UUID) -> ProjectVirtualLabMapping:  # ruff:ignore[no-self-use, unused-method-argument]
        msg = "Virtual lab API is not available when APP_DISABLE_AUTH is enabled."
        raise RuntimeError(msg)

    def close(self) -> None:
        """No underlying resource to release."""


def resolve_virtual_lab_id(user_context: UserContext, project_id: uuid.UUID) -> uuid.UUID:
    """Resolve the virtual lab id from the user context, raising if not found.

    When ``APP_DISABLE_AUTH`` is enabled it falls back to the header virtual lab id or the
    ``APP_DISABLE_AUTH_VIRTUAL_LAB_ID`` default, since Keycloak is unavailable in local dev.
    """
    if settings.APP_DISABLE_AUTH:
        return user_context.virtual_lab_id or settings.APP_DISABLE_AUTH_VIRTUAL_LAB_ID
    vlab_id = user_context.find_virtual_lab_from_project_id(project_id=project_id)
    if vlab_id is None:
        raise ApiError(
            message="Virtual lab id not found from project id in user groups.",
            error_code=ApiErrorCode.ASSET_VIRTUAL_LAB_ID_NOT_FOUND,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    return vlab_id
