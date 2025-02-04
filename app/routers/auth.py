from typing import Annotated

import httpx
from fastapi import Depends, HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from app.config import settings
from app.logger import L
from app.routers.types import ProjectContextHeader
from app.schemas.base import ProjectContext

AuthHeader: HTTPBearer = HTTPBearer(auto_error=True)


def check_project_id(
    project_context: ProjectContextHeader,
    token: Annotated[HTTPAuthorizationCredentials, Depends(AuthHeader)],
) -> bool:
    with httpx.Client() as client:
        tok = f"{token.scheme} {token.credentials}"
        response = client.get(
            settings.VLAB_API + "virtual-labs/projects",
            headers={"Authorization": tok},
            params={"size": 1000},
        )

        if response.status_code != 200:  # noqa: PLR2004
            L.warning("Could not check project_id: `%s`", response.text)
            raise HTTPException(status_code=404, detail="Project not found")

        projects = response.json()["data"]["results"]
        if any(res["id"] == project_context.project_id for res in projects):
            return True

        L.warning(
            "User attempted to use project_id %s, but is only a member of %s",
            project_context.project_id,
            [res["id"] for res in projects],
        )

    return False


def verify_project_id(
    is_project_id_allowed: Annotated[bool, Depends(check_project_id)],
    project_context: ProjectContextHeader,
) -> ProjectContextHeader:
    """Ensures that the user is authenticated and authorized.

    ie: as a member of the virtual_lab_id claimed in the header
    """
    if is_project_id_allowed:
        return project_context

    raise HTTPException(status_code=404, detail="Project not found")


AuthProjectContextHeader = Annotated[ProjectContext, Depends(verify_project_id)]
