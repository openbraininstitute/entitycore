from pydantic import BaseModel


from app.schemas.base import (
    CreationMixin,
)


class RoleBase(BaseModel):
    name: str
    role_id: str

    class Config:
        orm_mode = True
        from_attributes = True


class RoleCreate(RoleBase):
    pass


class RoleRead(RoleBase, CreationMixin):
    pass
