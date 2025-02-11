from typing import Annotated

import httpx
from fastapi import Depends, Header, HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from app.config import settings
from app.logger import L
from app.schemas.base import ProjectContext

AuthHeader: HTTPBearer = HTTPBearer(auto_error=True)
ProjectContextHeader = Annotated[ProjectContext, Header()]

KEYCLOAK_GROUPS_URL = settings.KEYCLOAK_URL + "protocol/openid-connect/userinfo"


def _split_out_vlab_and_projects(groups: list[str]) -> list[ProjectContext]:
    # "/proj/03ecd74b-a19e-4b3d-b737-5286a5fbea2d/6f945641-bc92-4e30-aa32-63be8eb9ca49/admin",
    result = []
    for group in groups:
        if not group.startswith("/proj/"):
            continue
        parts = group[6:].split("/")
        if len(parts) >= 3:  # noqa: PLR2004
            # pydantic checks to make sure that the IDs are UUID4
            result.append(ProjectContext(virtual_lab_id=parts[0], project_id=parts[1]))  # type: ignore[arg-type]
    return result


def check_project_id(
    project_context: ProjectContextHeader,
    token: Annotated[HTTPAuthorizationCredentials, Depends(AuthHeader)],
) -> bool:
    with httpx.Client() as client:
        tok = f"{token.scheme} {token.credentials}"
        response = client.get(
            KEYCLOAK_GROUPS_URL,
            headers={"Authorization": tok},
        )

        # response should look like:
        # {
        #  "email": "michael.gevaert@epfl.ch",
        #  "email_verified": false,
        #  "family_name": "Gevaert",
        #  "given_name": "Mike",
        #  "groups": [
        #      "/BBP-USERS",
        #      "/proj/$vlab_id/$project_id/admin",
        #      [...]
        #      "/vlab/$vlab_id/admin",
        #      [...]
        #  ],
        #  "name": "Mike Gevaert",
        #  "preferred_username": "mgeplf",
        #  "sub": "9856a4d6-005d-4cf9-b272-00b34661ef73"
        # }

        if response.status_code != 200:  # noqa: PLR2004
            L.warning("Keycloak returned an error: `{}`", response.text)
            raise HTTPException(status_code=404, detail="Project not found")

        data = response.json()
        if "groups" not in data:
            L.warning("Keycloak returned no `groups`: `{}`", response.text)
            raise HTTPException(status_code=404, detail="Project not found")

        projects = _split_out_vlab_and_projects(data["groups"])

        if any(project == project_context for project in projects):
            return True

        L.warning(
            "User attempted to use project_id {}, but is only a member of {}",
            project_context.project_id,
            [project.project_id for project in projects],
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
