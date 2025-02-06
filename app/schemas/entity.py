from pydantic import BaseModel, ConfigDict

from app.schemas.agent import AgentRead


class EntityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    createdBy: AgentRead | None
    createdBy_id: int | None
    updatedBy: AgentRead | None
    updatedBy_id: int | None
