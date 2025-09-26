import uuid
from typing import Annotated

import sqlalchemy as sa
from pydantic import AnyUrl, BaseModel, ConfigDict, Field, HttpUrl, PlainSerializer, computed_field
from sqlalchemy.orm import DeclarativeBase


class PaginationRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page: Annotated[int, Field(ge=1)] = 1
    page_size: Annotated[int, Field(ge=1)] = 100

    @computed_field
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page: int
    page_size: int
    total_items: int


class Facet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | int  # int is for brain region
    label: str
    count: int
    type: str | None


type Facets = dict[str, list[Facet]]


class ListResponse[M: BaseModel](BaseModel):
    data: list[M]
    pagination: PaginationResponse
    facets: Facets | None = None


type Select[M: DeclarativeBase] = sa.Select[tuple[M]]


# The URL's encoded string, using the punycode-encoded host for serialization to the db.
SerializableHttpUrl = Annotated[
    HttpUrl,
    PlainSerializer(lambda x: x.encoded_string(), return_type=str, when_used="unless-none"),
]
SerializableAnyUrl = Annotated[
    AnyUrl,
    PlainSerializer(lambda x: x.encoded_string(), return_type=str, when_used="unless-none"),
]


class PythonDependency(BaseModel):
    """Python dependency."""

    version: str  # e.g. ">=3.10,<3.12"


class DockerDependency(BaseModel):
    """Docker dependency."""

    image_repository: str  # e.g. "obi-notebook-image"
    image_tag: str | None = None  # e.g. ">=2025.09.24-2"
    image_digest: str | None = None  # SHA256 digest
    docker_version: str | None = None  # e.g. ">=20.10,<29.0"


class PythonRuntimeInfo(BaseModel):
    """Python runtime information."""

    version: str  # platform.python_version()
    implementation: str  # platform.python_implementation()
    executable: str  # sys.executable


class DockerRuntimeInfo(BaseModel):
    """Docker runtime information."""

    image_repository: str  # e.g. "public.ecr.aws/openbraininstitute/obi-notebook-image"
    image_tag: str  # e.g. "2025.09.24-2"
    image_digest: str | None = None  # SHA256 digest
    docker_version: str | None = None  # e.g. "28.4.0"


class OsRuntimeInfo(BaseModel):
    """OS runtime information."""

    system: str  # platform.system()
    release: str  # platform.release()
    version: str  # platform.version()
    machine: str  # platform.machine()
    processor: str  # platform.processor()


class RuntimeInfo(BaseModel):
    """Runtime information."""

    schema_version: int = 1
    python: PythonRuntimeInfo
    docker: DockerRuntimeInfo | None = None
    os: OsRuntimeInfo | None = None
