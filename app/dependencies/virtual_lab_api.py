from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials

from app.config import settings
from app.dependencies.auth import AdminContextDep, AuthHeader
from app.utils.virtual_lab import (
    AdminVirtualLabClient,
    AdminVirtualLabClientProtocol,
    DisabledAuthVirtualLabClient,
)


def get_admin_virtual_lab_client(
    _user_context: AdminContextDep,
    token: Annotated[HTTPAuthorizationCredentials | None, Depends(AuthHeader)],
) -> Iterator[AdminVirtualLabClientProtocol]:
    """Yield an admin client for the virtual lab API and close it after the request.

    Note: Virtual lab admin is determined by entitycore admin role.

    When ``APP_DISABLE_AUTH`` is enabled a no-op client is yielded, as the virtual lab API is
    not available in local dev and the virtual lab id is resolved from the headers instead.
    """
    if settings.APP_DISABLE_AUTH:
        yield DisabledAuthVirtualLabClient()
        return
    client = AdminVirtualLabClient(
        base_url=settings.VIRTUAL_LAB_API_URL,
        token=token.credentials if token else "",
    )
    try:
        yield client
    finally:
        client.close()


AdminVirtualLabClientDep = Annotated[
    AdminVirtualLabClientProtocol,
    Depends(get_admin_virtual_lab_client),
]
