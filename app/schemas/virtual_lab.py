from uuid import UUID

from app.schemas.base import Schema


class ProjectVirtualLabMapping(Schema):
    project_id: UUID
    virtual_lab_id: UUID
