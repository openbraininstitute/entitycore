import strawberry

from app.schemas.role import RoleRead


@strawberry.experimental.pydantic.type(model=RoleRead, all_fields=True)
class RoleReadType:
    pass
