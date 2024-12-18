from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.dependencies.db import get_db
import os
import json
import urllib.parse
router = APIRouter(
    prefix="/nexus/v1/files",
    tags=["legacy_files"],
)

@router.get("/{path:path}")
def legacy_files(path: str, request: Request, db: Session = Depends(get_db)):
    print(f"files endpoint: {path}")
    print(f"request headers: {request.headers.get('content-type', "")}")
    directory = "/".join(path.split("/", 2)[:2])
    file_name = "/".join(path.split("/", 2)[2:])
    encoded_filename = urllib.parse.quote(file_name, safe=":")
    with open(os.path.join(os.path.dirname(__file__), "files_data", directory, encoded_filename), "r") as f:
        try:
            data = json.load(f)
            return JSONResponse(content=data)
        except json.JSONDecodeError:
            return f.read()