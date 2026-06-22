import uuid

from app.schemas.base import Schema


class DeleteResponse(Schema):
    id: uuid.UUID
