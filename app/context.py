from contextvars import ContextVar
from typing import TypedDict


class RequestContext(TypedDict, total=False):
    """Request context dictionary."""

    request_id: str  # Unique identifier for the current request
    user_id: str  # Keycloak identifier of the user making the request


request_context_provider: ContextVar[RequestContext] = ContextVar("request_context")
