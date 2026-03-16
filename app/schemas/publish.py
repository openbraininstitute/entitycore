import uuid
from typing import Annotated

from pydantic import BaseModel, Field


class MoveFileResult(BaseModel):
    size: Annotated[int, Field(description="Size of the file")]
    error: str | None = None


class MoveDirectoryResult(BaseModel):
    size: Annotated[int, Field(description="Size of moved files in the directory")] = 0
    file_count: Annotated[int, Field(description="Number of moved files in the directory")] = 0
    errors: list[str] = []

    def update_from_file_result(self, file_result: MoveFileResult) -> None:
        self.size += file_result.size
        self.file_count += 1
        if file_result.error:
            self.errors.append(file_result.error)


class MoveAssetsResult(BaseModel):
    total_size: Annotated[int, Field(description="Total size of moved files")] = 0
    file_count: Annotated[int, Field(description="Number of moved files")] = 0
    asset_count: Annotated[int, Field(description="Number of updated assets")] = 0
    errors: list[str] = []

    def update_from_file_result(self, file_result: MoveFileResult) -> None:
        self.total_size += file_result.size
        self.file_count += 1
        self.asset_count += 1
        if file_result.error:
            self.errors.append(file_result.error)

    def update_from_directory_result(self, directory_result: MoveDirectoryResult) -> None:
        self.total_size += directory_result.size
        self.file_count += directory_result.file_count
        self.asset_count += 1
        self.errors.extend(directory_result.errors)


class ChangeProjectVisibilityResponse(BaseModel):
    """Successful response to the publish or unpublish operation."""

    message: Annotated[str, Field(description="A human-readable message describing the result")]
    project_id: Annotated[uuid.UUID, Field(description="ID of the project")]
    public: Annotated[bool, Field(description="Whether the content is now public or private")]
    resource_count: Annotated[
        int,
        Field(description="Number of updated resources (activities, entities, classifications)"),
    ]
    move_assets_result: Annotated[
        MoveAssetsResult, Field(description="Result of the assets movement")
    ]
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
