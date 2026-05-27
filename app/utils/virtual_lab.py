from uuid import UUID

import httpx

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
            url=f"/projects/{project_id}/virtual-lab",
            http_client=self._http_client,
            method="GET",
        )
        return ProjectVirtualLabMapping.model_validate(response.json()["data"])
