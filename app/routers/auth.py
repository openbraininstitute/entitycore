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

"""
http get https://openbluebrain.com//auth/realms/SBO/protocol/openid-connect/userinfo "Authorization:Bearer $TOKEN"
{
    "email": "michael.gevaert@epfl.ch",
    "email_verified": false,
    "family_name": "Gevaert",
    "given_name": "Mike",
    "groups": [
        "/BBP-USERS",
        "/proj/03ecd74b-a19e-4b3d-b737-5286a5fbea2d/6f945641-bc92-4e30-aa32-63be8eb9ca49/admin",
        "/proj/0bf0d7f2-c64d-48f5-8834-a974809d649a/a2435a39-6be7-4ba2-b819-ffc3f7f291b1/admin",
        "/proj/4f37eb04-bf73-441d-91b8-aae75bc6daea/23b4cfa9-c148-4531-a90b-9831841524c6/admin",
        "/proj/a6475ba9-ffd5-4fd2-a0d7-8d23125f3611/fe2db29c-742e-44bc-9543-8fa15e1590df/admin",
        "/proj/aaf1e861-1e7a-44bb-881d-b57e726ccdd4/82b09ad2-6a42-4a5e-81aa-2faacb25aa68/admin",
        "/proj/e58b7dcd-32a7-4b7c-8a87-764f02cb718a/006428a8-1f49-4f7c-906e-dd12107fa29e/admin",
        "/proj/e58b7dcd-32a7-4b7c-8a87-764f02cb718a/1d5a9fb1-50b6-44a7-8256-bd06ac0ff5fb/admin",
        "/proj/ea052b15-c3c6-48d9-83b7-5deaa4a26357/ee86d4a0-eaca-48ca-9788-ddc450250b15/admin",
        "/vlab/03ecd74b-a19e-4b3d-b737-5286a5fbea2d/admin",
        "/vlab/0bf0d7f2-c64d-48f5-8834-a974809d649a/admin",
        "/vlab/4f37eb04-bf73-441d-91b8-aae75bc6daea/admin",
        "/vlab/a6475ba9-ffd5-4fd2-a0d7-8d23125f3611/admin",
        "/vlab/aaf1e861-1e7a-44bb-881d-b57e726ccdd4/admin",
        "/vlab/d13aa588-662e-4305-aa53-90743048fcf0/admin",
        "/vlab/e58b7dcd-32a7-4b7c-8a87-764f02cb718a/admin",
        "/vlab/ea052b15-c3c6-48d9-83b7-5deaa4a26357/admin",
        "/vlab/f4b5aab0-64a5-468a-b890-1898f6b3efc4/admin"
    ],
    "name": "Mike Gevaert",
    "preferred_username": "mgeplf",
    "sub": "9856a4d6-005d-4cf9-b272-00b34661ef73"
}
"""

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
