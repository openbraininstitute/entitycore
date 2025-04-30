import hashlib
from pathlib import Path


def get_size_digest(file_path: Path) -> tuple[int, str]:
    """Return file size and hexdigest of file."""
    file_size = file_path.stat().st_size
    with file_path.open(mode="rb") as f:
        file_digest = hashlib.file_digest(f, "sha256").hexdigest()

    return file_size, file_digest


def get_output_asset_file_path(asset, out_dir: Path) -> Path:
    assert "/" not in asset.path
    return out_dir / f"{asset.id}__{asset.path}"
