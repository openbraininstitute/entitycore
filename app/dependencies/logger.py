from collections.abc import AsyncIterator

from starlette.requests import Request

from app.dependencies.auth import UserContextDep
from app.logger import L
from app.schemas.types import HeaderKey
from app.utils.uuid import create_uuid


async def logger_context(request: Request, user_context: UserContextDep) -> AsyncIterator[None]:
    """Add context information to each log message, different in each request.

    The additional keys are added to the extra dict.

    Must be async because FastAPI wraps sync generator dependencies with
    contextmanager_in_threadpool, which runs __enter__ and __exit__
    in different contexts, invalidating ContextVar tokens.
    See: https://github.com/fastapi/fastapi/blob/c441583/fastapi/concurrency.py#L28-L41
    """
    sub_id = user_context.profile.subject
    request_id = request.headers.get(HeaderKey.request_id) or create_uuid()
    forwarded_for = request.headers.get(HeaderKey.forwarded_for)

    with L.contextualize(
        sub_id=sub_id,
        request_id=request_id,
        forwarded_for=forwarded_for,
    ):
        yield
