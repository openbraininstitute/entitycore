from pydantic import BaseModel


class NmodlParameters(BaseModel):
    range: list[str]
    read: list[str]
    suffix: str
    point_process: str
    useion: list[str]
    write: list[str]
    nonspecific: list[str]
    valence: int
