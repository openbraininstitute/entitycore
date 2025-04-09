from pydantic import BaseModel


class NmodlParameters(BaseModel):
    range: list[str]
    read: list[str] | None = None
    suffix: str | None = None
    point_process: str | None = None
    useion: list[str] | None = None
    write: list[str] | None = None
    nonspecific: list[str] | None = None
    valence: int | None = None
