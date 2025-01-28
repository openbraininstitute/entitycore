import json
import urllib.parse
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(
    prefix="/nexus/v1/files",
    tags=["legacy_files"],
)


@router.get("/{path:path}")
def legacy_files(path: str):
    directory = "/".join(path.split("/", 2)[:2])
    file_name = "/".join(path.split("/", 2)[2:])
    encoded_filename = urllib.parse.quote(file_name, safe=":")
    with (Path(__file__).parent / "files_data" / directory / encoded_filename).open() as f:
        try:
            data = json.load(f)
            return JSONResponse(content=data)
        except json.JSONDecodeError:
            return f.read()
