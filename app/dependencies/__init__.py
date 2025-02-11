from typing import Annotated

from fastapi import Depends

from app.routers.auth import verify_project_id
from app.schemas.base import ProjectContext

AuthProjectContextHeader = Annotated[ProjectContext, Depends(verify_project_id)]
