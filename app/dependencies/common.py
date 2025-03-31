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

    def traverse(dependant: Dependant, params: dict[str, bool]) -> dict[str, bool]:
        """Update params from the query_params of all the dependencies.

        Return a dict of all the known params and the boolean values of `include_in_schema`.
        """
        params.update(
            (param.alias, getattr(param.field_info, "include_in_schema", True))
            for param in dependant.query_params
        )
        for dependency in dependant.dependencies:
            traverse(dependency, params)
        return params

    if allow_extra_params:
        return

    # possible improvement: cache allowed_params by request.scope["method"], request.scope["path"]
    allowed_params = traverse(request.scope["route"].dependant, params={})
    query_params = set(request.query_params.keys())
    if unknown_params := query_params.difference(allowed_params):
        raise ApiError(
            message="Unknown query parameters",
            error_code=ApiErrorCode.INVALID_REQUEST,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            details={
                "unknown_params": sorted(unknown_params),
                "allowed_params": sorted(
                    param
                    for param, include_in_schema in allowed_params.items()
                    if include_in_schema
                ),
            },
        )


PaginationQuery = Annotated[PaginationRequest, Depends(PaginationRequest)]
