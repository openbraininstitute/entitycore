import hashlib
import mimetypes

from fastapi import UploadFile

from app.db.types import ContentType
from app.logger import L


def get_content_type(file: UploadFile) -> ContentType:
    """Return the file content-type.

    In case of discrepancy with the original content-type, the discrepancy is just logged.

    We may decide normalize the original content-type, silently use the guessed content-type,
    or raise an error in case of discrepancy.

    For better guessing, read magic numbers to get the MIME type.
    """
    original_content_type = file.content_type
    (guessed_content_type, _content_encoding) = mimetypes.guess_type(
        file.filename or "", strict=False
    )
    if original_content_type != guessed_content_type:
        L.info(
            "File content type mismatch for {}: original={}, guessed={}",
            file.filename,
            original_content_type,
            guessed_content_type,
        )
    str_content_type = original_content_type or guessed_content_type
    return ContentType(str_content_type)


def calculate_sha256_digest(file: UploadFile) -> str:
    """Calculate the sha256 digest of the given file."""
    try:
        return hashlib.file_digest(file.file, "sha256").hexdigest()  # type: ignore[arg-type]
    finally:
        # Reset the file pointer to the beginning
        file.file.seek(0)
