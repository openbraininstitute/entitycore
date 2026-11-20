import hashlib
import threading
import time
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

import cachetools
import httpx2
from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials
from starlette.requests import Request

from app.config import settings
from app.context import request_context_provider
from app.dependencies.security import TokenDep
from app.errors import ApiError, ApiErrorCode, AuthErrorReason
from app.logger import L
from app.schemas.auth import (
    CacheKey,
    DecodedToken,
    UserContext,
    UserContextBase,
    UserContextWithProjectId,
    UserInfoResponse,
    UserProfile,
)
from app.schemas.base import OptionalProjectContext
from app.utils.common import is_ascii
from app.utils.http import deserialize_response, make_http_request

KEYCLOAK_GROUPS_URL = f"{settings.KEYCLOAK_URL}/protocol/openid-connect/userinfo"

# HTTP status code and error code returned for each auth error reason
AUTH_ERROR_STATUS: dict[AuthErrorReason, tuple[int, ApiErrorCode]] = {
    AuthErrorReason.AUTH_TOKEN_MISSING: (401, ApiErrorCode.NOT_AUTHENTICATED),
    AuthErrorReason.AUTH_TOKEN_INVALID: (401, ApiErrorCode.NOT_AUTHENTICATED),
    AuthErrorReason.AUTH_TOKEN_EXPIRED: (401, ApiErrorCode.NOT_AUTHENTICATED),
    AuthErrorReason.NOT_AUTHENTICATED_USER: (401, ApiErrorCode.NOT_AUTHENTICATED),
    AuthErrorReason.UNKNOWN: (401, ApiErrorCode.NOT_AUTHENTICATED),
    AuthErrorReason.NOT_AUTHORIZED_USER: (403, ApiErrorCode.NOT_AUTHORIZED),
    AuthErrorReason.NOT_AUTHORIZED_PROJECT: (403, ApiErrorCode.NOT_AUTHORIZED),
    AuthErrorReason.PROJECT_REQUIRED: (403, ApiErrorCode.NOT_AUTHORIZED),
    AuthErrorReason.ADMIN_REQUIRED: (403, ApiErrorCode.NOT_AUTHORIZED),
}


def _auth_error(reason: AuthErrorReason) -> ApiError:
    """Return the error to be raised for the given auth error reason."""
    http_status_code, error_code = AUTH_ERROR_STATUS[reason]
    return ApiError(message=reason, error_code=error_code, http_status_code=http_status_code)


def _get_cache_key(
    *,
    project_context: OptionalProjectContext,
    token: HTTPAuthorizationCredentials,
    **_,
) -> CacheKey:
    """Return the cache key for the given parameters.

    The cache key includes also virtual-lab-id and project-id to force a new request to KeyCloak
    when they change. This should avoid using a stale cache when a new project is created or
    assigned to the user, and the user switches to that project.
    """
    return CacheKey(
        virtual_lab_id=project_context.virtual_lab_id,
        project_id=project_context.project_id,
        scheme=token.scheme.lower(),
        token_digest=hashlib.sha256(token.credentials.encode()).hexdigest(),
    )


def _get_cache_ttu(_key: CacheKey, value: UserContext, now: float) -> float:
    """Calculate the expiration time of an item at the time of insertion into the cache.

    Args:
        _key: cache key.
        value: cache value.
        now: current value of the timer function.
    """
    expiration = now + settings.AUTH_CACHE_MAX_TTL
    if value.expiration and value.expiration > now:
        # consider the token expiration also when the user isn't authorized for the project,
        # so that a cached context never outlives the token
        expiration = min(expiration, value.expiration)
    L.opt(lazy=True).debug(
        "Setting cache expiration to {} for {}",
        lambda: datetime.fromtimestamp(expiration, tz=UTC).isoformat(),
        value.model_dump_json,
    )
    return expiration


@cachetools.cached(
    cache=cachetools.TLRUCache(
        maxsize=settings.AUTH_CACHE_MAXSIZE,
        ttu=_get_cache_ttu,
        timer=time.time,
    ),
    key=_get_cache_key,
    lock=threading.Lock(),
    info=settings.AUTH_CACHE_INFO,
)
def _check_user_info(
    *,
    project_context: OptionalProjectContext,
    token: HTTPAuthorizationCredentials,
    http_client: httpx2.Client,
) -> UserContext:
    """Retrieve the user info from KeyCloak and check the correctness of ProjectContext.

    Note that the result is cached, but exceptions are NOT cached.
    """
    decoded = DecodedToken.from_jwt(token)
    if decoded and decoded.exp and decoded.exp < time.time():
        # expired token, no need to call KeyCloak
        return UserContext(
            profile=UserProfile.from_user_info(decoded),
            expiration=decoded.exp,
            is_authorized=False,
            virtual_lab_id=project_context.virtual_lab_id,
            project_id=project_context.project_id,
            auth_error_reason=AuthErrorReason.AUTH_TOKEN_EXPIRED,
        )

    http_status_errors = {
        401: AuthErrorReason.NOT_AUTHENTICATED_USER,
        403: AuthErrorReason.NOT_AUTHORIZED_USER,
    }
    response = make_http_request(
        KEYCLOAK_GROUPS_URL,
        method="GET",
        headers={"Authorization": f"{token.scheme} {token.credentials}"},
        http_client=http_client,
        ignored_errors=set(http_status_errors),
    )

    if response.status_code in http_status_errors:
        return UserContext(
            profile=UserProfile.from_user_info(decoded) if decoded else UserProfile.unknown(),
            expiration=decoded.exp if decoded else None,
            is_authorized=False,
            virtual_lab_id=project_context.virtual_lab_id,
            project_id=project_context.project_id,
            auth_error_reason=http_status_errors[response.status_code],
        )

    user_info_response = deserialize_response(response, model_class=UserInfoResponse)

    if project_context.virtual_lab_id is None and project_context.project_id is not None:
        project_context.virtual_lab_id = user_info_response.virtual_lab_from_project_id(
            project_context.project_id
        )

    is_authorized = user_info_response.is_authorized_for(
        virtual_lab_id=project_context.virtual_lab_id,
        project_id=project_context.project_id,
    )

    is_service_admin = user_info_response.is_service_admin(settings.APP_NAME)
    is_service_maintainer = user_info_response.is_service_maintainer(settings.APP_NAME)

    user_context = UserContext(
        profile=UserProfile.from_user_info(user_info_response),
        expiration=decoded.exp if decoded else None,
        is_authorized=is_authorized,
        is_service_admin=is_service_admin,
        is_service_maintainer=is_service_maintainer,
        virtual_lab_id=project_context.virtual_lab_id,
        project_id=project_context.project_id,
        auth_error_reason=AuthErrorReason.NOT_AUTHORIZED_PROJECT if not is_authorized else None,
        user_project_groups=list(user_info_response.user_project_groups()),
    )

    if not user_context.is_authorized:
        L.opt(lazy=True, capture=False).info(
            "User <{name}> with sub <{sub}> attempted to use: "
            "virtual-lab-id={virtual_lab_id}, project-id={project_id} "
            "but they're only a member of {groups}",
            name=lambda: user_context.profile.name if user_context.profile else None,
            sub=lambda: user_context.profile.subject if user_context.profile else None,
            virtual_lab_id=lambda: project_context.virtual_lab_id,
            project_id=lambda: project_context.project_id,
            groups=lambda: sorted(user_info_response.groups),
        )

    return user_context


def _enrich_request_context(user_context: UserContext) -> None:
    """Store user_id in contextvar for logging purposes."""
    ctx = request_context_provider.get()
    ctx["user_id"] = str(user_context.profile.subject)


def _disabled_auth_virtual_lab_id(project_context: OptionalProjectContext) -> UUID | None:
    """Return the virtual lab when auth is disabled: a default if only project-id is given."""
    if project_context.virtual_lab_id or not project_context.project_id:
        return project_context.virtual_lab_id
    return settings.APP_DISABLE_AUTH_VIRTUAL_LAB_ID


def _authenticate(
    project_context: OptionalProjectContext,
    token: HTTPAuthorizationCredentials | None,
    request: Request,
) -> UserContext:
    """Authenticate the user with KeyCloak, and return the user context.

    Only a missing or invalid token raises an error here. The other errors, including the missing
    membership of the virtual lab and project in the headers, are in `auth_error_reason` of the
    returned context, and the calling dependency raises them.

    Args:
        project_context: virtual-lab-id and project-id from the headers.
        token: the auth token.
        request: the request, used to get the shared http client.
    """
    if settings.APP_DISABLE_AUTH:
        L.warning("Authentication is disabled: admin role granted, vlab and proj not verified")
        user_context = UserContext(
            profile=UserProfile(
                subject=UUID(int=0),
                name="Admin User",
            ),
            expiration=None,
            is_authorized=True,
            is_service_admin=True,
            is_service_maintainer=True,
            virtual_lab_id=_disabled_auth_virtual_lab_id(project_context),
            project_id=project_context.project_id,
        )
        # enrich request context even when the authentication is disabled
        _enrich_request_context(user_context)
        return user_context

    if not token:
        raise _auth_error(AuthErrorReason.AUTH_TOKEN_MISSING)
    if not token.credentials or not is_ascii(token.credentials):
        # non-ascii headers would raise an error in httpx when calling KeyCloak
        raise _auth_error(AuthErrorReason.AUTH_TOKEN_INVALID)

    user_context = _check_user_info(
        project_context=project_context,
        token=token,
        http_client=request.state.http_client,
    )

    # enrich request context before the calling dependency potentially raises an exception
    _enrich_request_context(user_context)

    return user_context


def _raise_for_auth_error(user_context: UserContext) -> None:
    """Raise an error if the user isn't authorized."""
    if not user_context.is_authorized:
        raise _auth_error(user_context.auth_error_reason or AuthErrorReason.UNKNOWN)


def _require_service_admin(user_context: UserContextBase) -> None:
    """Raise an error if the authenticated user doesn't have the service admin role."""
    if not user_context.is_service_admin:
        raise _auth_error(AuthErrorReason.ADMIN_REQUIRED)


def _require_project_id(user_context: UserContext) -> None:
    """Raise an error if virtual_lab_id or project_id is missing."""
    if not user_context.virtual_lab_id or not user_context.project_id:
        raise _auth_error(AuthErrorReason.PROJECT_REQUIRED)


def user_verified(
    project_context: Annotated[OptionalProjectContext, Header()],
    token: TokenDep,
    request: Request,
) -> UserContext:
    """Ensure that the user is authenticated and a member of the project in the headers.

    The membership of virtual-lab-id and project-id is checked only when they're given.
    """
    user_context = _authenticate(project_context=project_context, token=token, request=request)
    _raise_for_auth_error(user_context)
    return user_context


def user_with_service_admin_role(
    token: TokenDep,
    request: Request,
) -> UserContext:
    """Ensure that the user is authenticated and has the service admin role.

    The project headers are ignored: admins don't need to be members of any project.
    """
    user_context = _authenticate(
        project_context=OptionalProjectContext(), token=token, request=request
    )
    _raise_for_auth_error(user_context)
    _require_service_admin(user_context)
    return user_context


def user_with_project_id(
    user_context: UserContextDep,
) -> UserContextWithProjectId:
    """Ensure that the authenticated user has valid virtual_lab_id and project_id."""
    _require_project_id(user_context)
    return UserContextWithProjectId.model_validate(user_context)


def user_with_service_admin_role_and_project_id(
    user_context: UserContextWithProjectIdDep,
) -> UserContextWithProjectId:
    """Ensure that the user is a service admin and a member of the project in the headers.

    Used only on the user routes: the admin routes ignore the project headers.
    """
    _require_service_admin(user_context)
    return user_context


UserContextDep = Annotated[UserContext, Depends(user_verified)]
AdminContextDep = Annotated[UserContext, Depends(user_with_service_admin_role)]
UserContextWithProjectIdDep = Annotated[
    UserContextWithProjectId,
    Depends(user_with_project_id),
]
AdminContextWithProjectIdDep = Annotated[
    UserContextWithProjectId,
    Depends(user_with_service_admin_role_and_project_id),
]
