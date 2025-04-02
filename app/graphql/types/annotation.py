import strawberry

from app.schemas.annotation import Annotation


@strawberry.experimental.pydantic.type(model=Annotation, all_fields=True)
class AnnotationType:
    pass
