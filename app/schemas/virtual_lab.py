from uuid import UUID

from pydantic import BaseModel


class ProjectVirtualLabMapping(BaseModel):
    project_id: UUID
    virtual_lab_id: UUID
