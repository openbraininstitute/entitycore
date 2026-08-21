from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials

from app.config import settings
from app.dependencies.auth import AdminContextDep, AuthHeader
from app.utils.virtual_lab import AdminVirtualLabClient


def get_admin_virtual_lab_client(
    _user_context: AdminContextDep,
    token: Annotated[HTTPAuthorizationCredentials, Depends(AuthHeader)],
) -> Iterator[AdminVirtualLabClient]:
    """Yield an admin client for the virtual lab API and close it after the request.

    Note: Virtual lab admin is determined by entitycore admin role.
    """
    client = AdminVirtualLabClient(
        base_url=settings.VIRTUAL_LAB_API_URL,
        token=token.credentials,
    )
    try:
        yield client
    finally:
        client.close()


AdminVirtualLabClientDep = Annotated[
    AdminVirtualLabClient,
    Depends(get_admin_virtual_lab_client),
]
