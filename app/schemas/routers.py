import uuid

from pydantic import BaseModel, ConfigDict


class DeleteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
