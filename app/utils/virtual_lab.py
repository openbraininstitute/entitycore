import uuid
from http import HTTPStatus
from uuid import UUID

import httpx

from app.errors import ApiError, ApiErrorCode
from app.schemas.auth import UserContext
from app.schemas.virtual_lab import ProjectVirtualLabMapping
from app.utils.http import make_http_request


class VirtualLabClient:
    """Client for virtual lab api user endpoints."""

    def __init__(self, base_url: str, token: str) -> None:
        """Instantiate client for virtual lab api."""
        self._http_client = httpx.Client(
            base_url=base_url, headers={"Authorization": f"Bearer {token}"}
        )


class AdminVirtualLabClient(VirtualLabClient):
    def get_virtual_lab_by_project(self, project_id: UUID) -> ProjectVirtualLabMapping:
        response = make_http_request(
            url=f"/virtual-labs/projects/{project_id}/virtual-lab",
            http_client=self._http_client,
            method="GET",
        )
        return ProjectVirtualLabMapping.model_validate(response.json()["data"])


def resolve_virtual_lab_id(user_context: UserContext, project_id: uuid.UUID) -> uuid.UUID:
    """Resolve the virtual lab id from the user context, raising if not found."""
    vlab_id = user_context.find_virtual_lab_from_project_id(project_id=project_id)
    if vlab_id is None:
        raise ApiError(
            message="Virtual lab id not found from project id in user groups.",
            error_code=ApiErrorCode.ASSET_VIRTUAL_LAB_ID_NOT_FOUND,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    return vlab_id
