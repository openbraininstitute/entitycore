from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.repository.group import RepositoryGroup


def get_db(request: Request) -> Iterator[Session]:
    """Yield a database session, to be used as a dependency."""
    with request.state.database_session_manager.session() as session:
        yield session


def _get_repo_group(db: "SessionDep") -> RepositoryGroup:
    """Return the repository group, to be used as a dependency."""
    return RepositoryGroup(db=db)


SessionDep = Annotated[Session, Depends(get_db)]
RepoGroupDep = Annotated[RepositoryGroup, Depends(_get_repo_group)]
