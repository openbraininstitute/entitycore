import pytest
from pydantic import ValidationError

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


@pytest.mark.parametrize(
    "name",
    ["SENTRY_TRACES_SAMPLE_RATE", "SENTRY_PROFILE_SESSION_SAMPLE_RATE"],
)
@pytest.mark.parametrize("value", [-0.1, 1.1])
def test_configs_invalid_sentry_sample_rate(name, value):
    with pytest.raises(ValidationError, match=name):
        Settings(**{name: value})
