from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session
from starlette.requests import Request


def get_db(request: Request) -> Iterator[Session]:
    """Yield a database session, to be used as a dependency."""
    with request.state.database_session_manager.session() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
