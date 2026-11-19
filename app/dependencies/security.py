"""Security schemes extracting the credentials from the request."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# auto_error=False because of https://github.com/fastapi/fastapi/issues/10177
AuthHeader: HTTPBearer = HTTPBearer(auto_error=False)

TokenDep = Annotated[HTTPAuthorizationCredentials | None, Depends(AuthHeader)]
