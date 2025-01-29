from typing import Annotated

from fastapi import Header

from app.schemas.base import ProjectContext


ProjectContextHeader = Annotated[ProjectContext, Header()]
