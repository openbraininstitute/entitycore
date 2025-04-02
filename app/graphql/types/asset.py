import strawberry

from app.schemas.asset import AssetRead


@strawberry.experimental.pydantic.type(model=AssetRead)
class AssetReadType:
    id: strawberry.auto
    status: strawberry.auto
    path: strawberry.auto
    full_path: strawberry.auto
    is_directory: strawberry.auto
    content_type: strawberry.auto
    size: strawberry.auto
    sha256_digest: strawberry.auto
    meta: strawberry.scalars.JSON
