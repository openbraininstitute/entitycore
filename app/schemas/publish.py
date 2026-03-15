import uuid
from typing import Annotated

from pydantic import BaseModel, Field


class ChangeProjectVisibilityResponse(BaseModel):
    """Successful response to the publish or unpublish operation."""

    message: Annotated[str, Field(description="A human-readable message describing the result")]
    project_id: Annotated[uuid.UUID, Field(description="ID of the project")]
    public: Annotated[bool, Field(description="Whether the content is now public or private")]
    resource_count: Annotated[
        int,
        Field(description="Number of updated resources (activities, entities, classifications)"),
    ]
    asset_count: Annotated[int, Field(description="Number of updated assets")]
    total_file_count: Annotated[int, Field(description="Number of moved files")]
    total_file_size: Annotated[int, Field(description="Total size of moved files")]
    dry_run: Annotated[bool, Field(description="True if the operation has been simulated only")]
    completed: Annotated[
        bool,
        Field(
            description=(
                "Whether the assets have been fully updated. It may be False if `max_assets` "
                "have been specified, and there are still assets to be moved."
            )
        ),
    ]
