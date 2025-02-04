from typing import Annotated
from uuid import UUID

from fastapi import Depends


def _get_project_id() -> UUID:
    # placeholder
    return UUID("00000000-0000-0000-0000-000000000001")


ProjectDep = Annotated[UUID, Depends(_get_project_id)]
