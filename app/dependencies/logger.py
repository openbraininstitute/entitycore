from collections.abc import AsyncIterator

from starlette.requests import Request

from app.dependencies.auth import UserContextDep
from app.logger import L
from app.schemas.types import HeaderKey


async def logger_context(request: Request, user_context: UserContextDep) -> AsyncIterator[None]:
    """Add context information to each log message in authenticated endpoints.

    It shold be used only in authenticated endpoints, since it depends on `user_context`.

    These additional keys are added to the extra dict:

    - sub_id: the subject_id from Keycloak
    - request_id: id that can be used to correlate multiple logs in the same request
    - forwarded_for: the originating IP address of the client, from the X-Forwarded-For HTTP header

    Must be async because FastAPI wraps sync generator dependencies with
    contextmanager_in_threadpool, which runs __enter__ and __exit__
    in different contexts, invalidating ContextVar tokens.
    See: https://github.com/fastapi/fastapi/blob/c441583/fastapi/concurrency.py#L28-L41
    """
    sub_id = str(user_context.profile.subject)
    request_id = request.state.request_id
    forwarded_for = request.headers.get(HeaderKey.forwarded_for)

    with L.contextualize(
        sub_id=sub_id,
        request_id=request_id,
        forwarded_for=forwarded_for,
    ):
        yield
