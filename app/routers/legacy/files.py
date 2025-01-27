import json
import os
import urllib.parse

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
    with open(
        os.path.join(os.path.dirname(__file__), "files_data", directory, encoded_filename),
    ) as f:
        try:
            data = json.load(f)
            return JSONResponse(content=data)
        except json.JSONDecodeError:
            return f.read()
