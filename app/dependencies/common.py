from http import HTTPStatus
from typing import Annotated

from fastapi import Depends, Query
from fastapi.dependencies.models import Dependant
from starlette.requests import Request

from app.errors import ApiError, ApiErrorCode
from app.schemas.types import PaginationRequest


def forbid_extra_query_params(
    request: Request,
    *,
    allow_extra_params: Annotated[bool, Query(include_in_schema=False)] = False,
) -> None:
    """Forbid extra query parameters.

    If needed, this can be disabled per request by setting the param `allow_extra_params=true`,
    but this option is intended for internal use, and it might be removed in the future.
    """

    def traverse(dependant: Dependant, params: set) -> set:
        """Update params from the query_params of all the dependencies."""
        params.update(param.alias for param in dependant.query_params)
        for dependency in dependant.dependencies:
            traverse(dependency, params)
        return params

    if allow_extra_params:
        return

    # allowed_params could be cached by (request.scope["method"], request.scope["path"])
    allowed_params = traverse(request.scope["route"].dependant, params=set())
    query_params = set(request.query_params.keys())
    if unknown_params := query_params - allowed_params:
        raise ApiError(
            message="Unknown query parameters",
            error_code=ApiErrorCode.INVALID_REQUEST,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            details={
                "unknown_params": sorted(unknown_params),
                "allowed_params": sorted(allowed_params - {"allow_extra_params"}),
            },
        )


PaginationQuery = Annotated[PaginationRequest, Depends(PaginationRequest)]
