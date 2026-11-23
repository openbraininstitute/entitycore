from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends

from app.config import settings
from app.dependencies.security import TokenDep
from app.utils.virtual_lab import (
    AdminVirtualLabClient,
    AdminVirtualLabClientProtocol,
    DisabledAuthVirtualLabClient,
)


def get_admin_virtual_lab_client(token: TokenDep) -> Iterator[AdminVirtualLabClientProtocol]:
    """Yield an admin client for the virtual lab API and close it after the request.

    Note: Virtual lab admin is determined by entitycore admin role, required by the callers.

    When ``APP_DISABLE_AUTH`` is enabled, the virtual lab API isn't available in local dev, and
    the yielded client maps every project to ``APP_DISABLE_AUTH_VIRTUAL_LAB_ID``.
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
