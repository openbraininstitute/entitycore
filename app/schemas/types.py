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

    version: Annotated[str, Field(examples=[">=3.10,<3.12"])]


class DockerDependency(BaseModel):
    """Docker dependency."""

    image_repository: Annotated[str, Field(examples=["openbraininstitute/obi-notebook-image"])]
    image_tag: Annotated[str | None, Field(examples=[">=2025.09.24-2"])] = None
    image_digest: Annotated[
        str | None,
        Field(
            description="SHA256 digest",
            examples=["3406990b6e4c7192317b6fdc5680498744f6142f01f0287f4ee0420d8c74063c"],
        ),
    ] = None
    docker_version: Annotated[str | None, Field(examples=[">=20.10,<29.0"])] = None


class PythonRuntimeInfo(BaseModel):
    """Python runtime information."""

    version: Annotated[
        str, Field(description="Output of `platform.python_version()`", examples=["3.9.21"])
    ]
    implementation: Annotated[
        str, Field(description="Output of `platform.python_implementation()`", examples=["CPython"])
    ]
    executable: Annotated[
        str, Field(description="Output of `sys.executable`", examples=["/usr/bin/python"])
    ]


class DockerRuntimeInfo(BaseModel):
    """Docker runtime information."""

    image_repository: Annotated[str, Field(examples=["openbraininstitute/obi-notebook-image"])]
    image_tag: Annotated[str, Field(examples=["2025.09.24-2"])]
    image_digest: Annotated[
        str | None,
        Field(
            description="SHA256 digest",
            examples=["3406990b6e4c7192317b6fdc5680498744f6142f01f0287f4ee0420d8c74063c"],
        ),
    ] = None
    docker_version: Annotated[str | None, Field(examples=["28.4.0"])] = None


class OsRuntimeInfo(BaseModel):
    """OS runtime information."""

    system: Annotated[str, Field(description="Output of `platform.system()`", examples=["Linux"])]
    release: Annotated[
        str,
        Field(
            description="Output of `platform.release()`",
            examples=["5.14.0-427.28.1.el9_4.x86_64"],
        ),
    ]
    version: Annotated[
        str,
        Field(
            description="Output of `platform.version()`",
            examples=["#1 SMP PREEMPT_DYNAMIC Fri Aug 2 03:44:10 EDT 2024"],
        ),
    ]
    machine: Annotated[
        str, Field(description="Output of `platform.machine()`", examples=["x86_64"])
    ]
    processor: Annotated[
        str, Field(description="Output of `platform.processor()`", examples=["x86_64"])
    ]


class RuntimeInfo(BaseModel):
    """Runtime information."""

    schema_version: int = 1
    python: PythonRuntimeInfo
    docker: DockerRuntimeInfo | None = None
    os: OsRuntimeInfo | None = None
