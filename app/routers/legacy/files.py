import json
import os
import urllib.parse

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.dependencies.db import get_db

router = APIRouter(
    prefix="/nexus/v1/files",
    tags=["legacy_files"],
)


@router.get("/{path:path}")
def legacy_files(path: str, request: Request, db: Session = Depends(get_db)):
    directory = "/".join(path.split("/", 2)[:2])
    file_name = "/".join(path.split("/", 2)[2:])
    encoded_filename = urllib.parse.quote(file_name, safe=":")
    with open(
        os.path.join(
            os.path.dirname(__file__), "files_data", directory, encoded_filename
        ),
    ) as f:
        try:
            data = json.load(f)
            return JSONResponse(content=data)
        except json.JSONDecodeError:
            return f.read()
