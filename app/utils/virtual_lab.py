import uuid
from http import HTTPStatus
from typing import Protocol
from uuid import UUID

import httpx2

from app.config import settings
from app.errors import ApiError, ApiErrorCode
from app.logger import L
from app.schemas.auth import UserContext
from app.schemas.virtual_lab import ProjectVirtualLabMapping
from app.utils.http import make_http_request

# virtual-lab-manager returns 403 also for unknown or deleted projects, instead of 404
PROJECT_NOT_FOUND_STATUS_CODES: set[int] = {HTTPStatus.FORBIDDEN, HTTPStatus.NOT_FOUND}


class AdminVirtualLabClientProtocol(Protocol):
    """Interface used by the service layer to resolve a virtual lab from a project."""

    def find_virtual_lab_by_project(self, project_id: UUID) -> ProjectVirtualLabMapping | None: ...

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
    def find_virtual_lab_by_project(self, project_id: UUID) -> ProjectVirtualLabMapping | None:
        """Return the virtual lab of the project, or None if the project isn't found."""
        response = make_http_request(
            url=f"/virtual-labs/projects/{project_id}/virtual-lab",
            http_client=self._http_client,
            method="GET",
            ignored_errors=PROJECT_NOT_FOUND_STATUS_CODES,
        )
        if response.status_code in PROJECT_NOT_FOUND_STATUS_CODES:
            # a 403 may also mean that the token was rejected, see virtual-lab-api#218
            L.warning(
                "Project {} not found in virtual-lab-manager: HTTP status {}",
                project_id,
                response.status_code,
            )
            return None
        return ProjectVirtualLabMapping.model_validate(response.json()["data"])


class DisabledAuthVirtualLabClient:
    """Admin client used when ``APP_DISABLE_AUTH`` is enabled.

    The virtual lab API is neither reachable nor authenticated in local dev, so every project is
    considered to exist, in the virtual lab ``APP_DISABLE_AUTH_VIRTUAL_LAB_ID``.
    """

    def find_virtual_lab_by_project(self, project_id: UUID) -> ProjectVirtualLabMapping | None:  # ruff:ignore[no-self-use]
        """Return the mapping of the project to the default virtual lab."""
        return ProjectVirtualLabMapping(
            project_id=project_id, virtual_lab_id=settings.APP_DISABLE_AUTH_VIRTUAL_LAB_ID
        )

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


def resolve_admin_virtual_lab_id(
    virtual_lab_client: AdminVirtualLabClientProtocol, project_id: uuid.UUID
) -> uuid.UUID:
    """Resolve the virtual lab id of the project with virtual-lab-manager, raising if not found."""
    mapping = virtual_lab_client.find_virtual_lab_by_project(project_id)
    if mapping is None:
        raise ApiError(
            message="Virtual lab id not found from project id in virtual-lab-manager.",
            error_code=ApiErrorCode.ASSET_VIRTUAL_LAB_ID_NOT_FOUND,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    return mapping.virtual_lab_id


def ensure_project_exists(
    virtual_lab_client: AdminVirtualLabClientProtocol, project_id: uuid.UUID
) -> None:
    """Raise an error if the project isn't found in virtual-lab-manager."""
    if virtual_lab_client.find_virtual_lab_by_project(project_id) is None:
        raise ApiError(
            message="Project not found",
            error_code=ApiErrorCode.PROJECT_NOT_FOUND,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
