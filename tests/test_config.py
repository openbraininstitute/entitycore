import pytest

from app.config import Settings


def test_multipart_upload_size_valid(monkeypatch):
    monkeypatch.setenv("S3_MULTIPART_UPLOAD_MAX_SIZE", str(5 * 1024**3))
    monkeypatch.setenv("S3_MULTIPART_UPLOAD_MAX_PART_SIZE", str(5 * 1024**2))
    monkeypatch.setenv("S3_MULTIPART_UPLOAD_MAX_PARTS", "2000")

    settings = Settings()

    assert settings.S3_MULTIPART_UPLOAD_MAX_SIZE <= (
        settings.S3_MULTIPART_UPLOAD_MAX_PART_SIZE * settings.S3_MULTIPART_UPLOAD_MAX_PARTS
    )


def test_multipart_upload_size_invalid(monkeypatch):
    monkeypatch.setenv("S3_MULTIPART_UPLOAD_MAX_SIZE", str(10 * 1024**3))
    monkeypatch.setenv("S3_MULTIPART_UPLOAD_MAX_PART_SIZE", str(5 * 1024**2))
    monkeypatch.setenv("S3_MULTIPART_UPLOAD_MAX_PARTS", "100")

    with pytest.raises(ValueError, match="S3 multipart upload max size outside allowed limits"):
        Settings()
