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


# Using Depends(scope="function"), the exit code after yield is executed right after the path
# operation function is finished, before the response is sent back to the client.
# In this way, the commit of the db transaction and the associated events
# are executed before the response is sent back to the client.
SessionDep = Annotated[Session, Depends(get_db, scope="function")]
RepoGroupDep = Annotated[RepositoryGroup, Depends(_get_repo_group)]
