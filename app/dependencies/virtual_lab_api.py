from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials

from app.config import settings
from app.dependencies.auth import AdminContextDep
from app.utils.virtual_lab import AdminVirtualLabClient


def get_admin_virtual_lab_client(
    _user_context: AdminContextDep,
    token: HTTPAuthorizationCredentials,
) -> AdminVirtualLabClient:
    """Return admin client for virtual lab api.

    Note: Virtual lab admin is determined by entitycore admin role.
    """
    return AdminVirtualLabClient(
        base_url=settings.VIRTUAL_LAB_API_URL,
        token=token.credentials,
    )


AdminVirtualLabClientDep = Annotated[
    AdminVirtualLabClient,
    Depends(get_admin_virtual_lab_client),
]
