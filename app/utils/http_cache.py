"""Utilities for HTTP caching with ETags."""

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from http import HTTPStatus
from typing import Self

from starlette.requests import Request
from starlette.responses import Response

from app.schemas.types import HeaderKey

# Weak ETag: same content, but the body can be compressed.
WEAK_ETAG_PREFIX = "W/"
NOT_MODIFIED_RESPONSE: dict[int | str, dict] = {
    HTTPStatus.NOT_MODIFIED: {"description": "Not modified, the ETag in If-None-Match is current"}
}


def make_cache_control(max_age_seconds: int = 0) -> str:
    """Return the Cache-Control value for a private response.

    Without max_age_seconds, clients can store the response but must revalidate it before
    using it. Otherwise, they can reuse it without asking the server for that many seconds.
    """
    if max_age_seconds <= 0:
        return "private, no-cache"
    return f"private, max-age={max_age_seconds}"


def make_etag(content: bytes) -> str:
    """Return a weak ETag for the given content."""
    return f'{WEAK_ETAG_PREFIX}"{hashlib.blake2b(content, digest_size=16).hexdigest()}"'


def etag_matches(if_none_match: str | None, etag: str) -> bool:
    """Return True if any ETag in If-None-Match matches the given ETag, with weak comparison."""
    if not if_none_match:
        return False
    if if_none_match.strip() == "*":
        return True
    opaque_tag = etag.removeprefix(WEAK_ETAG_PREFIX)
    return any(
        tag.strip().removeprefix(WEAK_ETAG_PREFIX) == opaque_tag for tag in if_none_match.split(",")
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class CachedJson:
    """Serialized JSON content, with its ETag."""

    content: bytes
    etag: str

    @classmethod
    def from_content(cls, content: bytes) -> Self:
        """Return a new instance, computing the ETag of the content."""
        return cls(content=content, etag=make_etag(content))

    def size(self) -> int:
        """Return the size of the content in bytes."""
        return len(self.content)

    def to_response(
        self, request: Request, *, max_age_seconds: int = 0, vary: Sequence[str] = ()
    ) -> Response:
        """Return a new response, or 304 Not Modified if the client already has the content.

        Args:
            request: The incoming request, used to evaluate If-None-Match.
            max_age_seconds: Seconds during which the client can reuse the content without
                asking the server. If 0, the client must revalidate it on every use.
            vary: Names of the request headers that change the content, for example
                ``("virtual-lab-id", "project-id")``.
        """
        headers: dict[str, str] = {
            HeaderKey.etag: self.etag,
            HeaderKey.cache_control: make_cache_control(max_age_seconds),
        }
        if vary:
            headers[HeaderKey.vary] = ", ".join(vary)
        if etag_matches(request.headers.get(HeaderKey.if_none_match), self.etag):
            return Response(status_code=HTTPStatus.NOT_MODIFIED, headers=headers)
        return Response(content=self.content, media_type="application/json", headers=headers)
