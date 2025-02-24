from typing import Annotated

from fastapi import Depends

from app.routers.types import PaginationRequest


def page_validation(page: int | None = None, page_size: int | None = None) -> PaginationRequest:
    return PaginationRequest(page=page or 0, page_size=page_size or 10)


PaginationQuery = Annotated[PaginationRequest, Depends(page_validation)]
