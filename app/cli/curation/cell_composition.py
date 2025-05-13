import json
from pathlib import Path

from app.cli.curation.utils import get_output_asset_file_path, get_size_digest
from app.cli.types import ContentType
from app.cli.utils import _find_by_legacy_id
from app.db.model import Asset, BrainRegion, ETypeClass, METypeDensity, MTypeClass
from app.db.types import AssetLabel, EntityType

MIN_NUM_ASSETS = 2


def curate_assets(
    *,
    db,
    src_paths: dict[str, str],
    assets: dict[ContentType, list[Asset]],
    out_dir: Path,
    is_dry_run: bool,
) -> dict[str, str]:
    """Transform CellComposition assets to entitycore compatible equivalents."""
    summary_asset, volumes_asset = _classify_assets(assets)
    summary_paths = _curate_summary_asset(
        db=db, asset=summary_asset, src_paths=src_paths, out_dir=out_dir, is_dry_run=is_dry_run
    )
    volumes_paths = _curate_volumes_asset(
        db=db, asset=volumes_asset, src_paths=src_paths, out_dir=out_dir, is_dry_run=is_dry_run
    )
    return summary_paths | volumes_paths


def _classify_assets(asset_dict: dict[ContentType, list[Asset]]) -> tuple[Asset, Asset]:
    """Classify CellComposition assets into summary and volumes."""
    json_assets = asset_dict.get(ContentType.json)
    if not json_assets or len(json_assets) < MIN_NUM_ASSETS:
        msg = "CellComposition curation expects at least 2 json assets."
        raise RuntimeError(msg)

    summary = volumes = None
    for asset in json_assets:
        if _is_summary_path(asset.path):
            summary = asset
        else:
            volumes = asset

    assert volumes is not None, "No volumes asset found in CellComposition."
    assert summary is not None, "No summary asset found in CellComposition."

    return summary, volumes


def _curate_summary_asset(
    *, db, asset: Asset, src_paths: dict[str, str], out_dir: Path, is_dry_run: bool
) -> dict[str, str]:
    """Transform CellComposition summary asset file to entitycore compatible equivalent."""
    assert asset.sha256_digest is not None
    source_file = Path(src_paths[asset.sha256_digest.hex()])
    source_data = _load_json(source_file)

    target_data = _transform_summary_data(db, source_data)
    target_file = get_output_asset_file_path(asset, out_dir)
    _write_json(data=target_data, path=target_file)

    new_size, new_digest = get_size_digest(target_file)

    if not is_dry_run:
        asset.size = new_size
        asset.content_type = ContentType.json
        asset.sha256_digest = bytes.fromhex(new_digest)
        asset.label = AssetLabel.cell_composition_summary

    return {new_digest: str(target_file)}


def _curate_volumes_asset(
    *, db, asset: Asset, src_paths: dict[str, str], out_dir: Path, is_dry_run: bool
) -> dict[str, str]:
    assert asset.sha256_digest is not None
    source_file = Path(src_paths[asset.sha256_digest.hex()])
    source_data = _load_json(source_file)

    target_data = _transform_volumes_data(db, source_data)
    target_file = get_output_asset_file_path(asset, out_dir)
    _write_json(data=target_data, path=target_file)

    new_size, new_digest = get_size_digest(target_file)

    if not is_dry_run:
        asset.size = new_size
        asset.content_type = ContentType.json
        asset.sha256_digest = bytes.fromhex(new_digest)
        asset.label = AssetLabel.cell_composition_volumes

    return {new_digest: str(target_file)}


def _is_summary_path(path: str) -> bool:
    name = path.lower()
    return "summary" in name or "stats" in name


def _load_json(path: Path) -> dict:
    return json.loads(Path(path).read_bytes())


def _transform_summary_data(db, data: dict) -> dict:
    new_region_data = dict(
        _transform_region_data_dict(db, region_data) for region_data in data["hasPart"].values()
    )
    return _copy_fields(data) | {"hasPart": new_region_data}


def _transform_region_data_dict(db, region_data: dict) -> tuple[str, dict]:
    db_region = _find_region(db, region_data["notation"])

    new_mtype_data = dict(
        _transform_mtype_data_dict(db, mtype_data) for mtype_data in region_data["hasPart"].values()
    )
    # overwite region keys with db data to enforce consistency
    return str(db_region.id), _copy_fields(region_data) | {
        "name": db_region.name,
        "notation": db_region.acronym,
        "hasPart": new_mtype_data,
    }


def _transform_mtype_data_dict(db, mtype_data: dict) -> tuple[str, dict]:
    db_mtype = _find_mtype(db, mtype_data["label"])
    new_etype_data = dict(
        _transform_etype_data_dict(db, etype_data) for etype_data in mtype_data["hasPart"].values()
    )
    # overwite mtype labels with db data to enforce consistency
    return str(db_mtype.id), _copy_fields(mtype_data) | {
        "label": db_mtype.pref_label,
        "hasPart": new_etype_data,
    }


def _transform_etype_data_dict(db, etype_data: dict) -> tuple[str, dict]:
    db_etype = _find_etype(db, etype_data["label"])
    return str(db_etype.id), etype_data | {"label": db_etype.pref_label}


def _transform_volumes_data(db, data: dict) -> dict:
    new_mtype_data = [_transform_mtype_data_list(db, mtype_data) for mtype_data in data["hasPart"]]

    return _copy_fields(data) | {"hasPart": new_mtype_data}


def _transform_mtype_data_list(db, data: dict) -> dict:
    db_mtype = _find_mtype(db, data["label"])
    new_etype_data = [_transform_etype_data_list(db, etype_data) for etype_data in data["hasPart"]]
    return {
        "@id": str(db_mtype.id),
        "@type": "mtype_class",
        "label": db_mtype.pref_label,
        "hasPart": new_etype_data,
    }


def _transform_etype_data_list(db, data: dict) -> dict:
    db_etype = _find_etype(db, data["label"])

    new_density_data = [
        _transform_density_data(db, density_data) for density_data in data["hasPart"]
    ]
    return {
        "@id": str(db_etype.id),
        "@type": "etype_class",
        "label": db_etype.pref_label,
        "hasPart": new_density_data,
    }


def _transform_density_data(db, data: dict) -> dict:
    db_density = _find_by_legacy_id(data["@id"], METypeDensity, db)
    return {"@id": str(db_density.id), "@type": EntityType.me_type_density.value}


def _find_region(db, acronym: str, _cache: dict = {}) -> BrainRegion:
    if cached := _cache.get(acronym):
        return cached

    if not (res := db.query(BrainRegion).filter(BrainRegion.acronym == acronym).first()):
        msg = f"Brain region {acronym} was not found in db."
        raise RuntimeError(msg)

    _cache[acronym] = res

    return res


def _find_mtype(db, label: str, _cache: dict = {}) -> MTypeClass:
    if cached := _cache.get(label):
        return cached

    if not (res := db.query(MTypeClass).filter(MTypeClass.pref_label == label).first()):
        msg = f"MType {label} was not found in db."
        raise RuntimeError(msg)

    _cache[label] = res

    return res


def _find_etype(db, label: str, _cache: dict = {}) -> ETypeClass:
    if cached := _cache.get(label):
        return cached

    if not (res := db.query(ETypeClass).filter(ETypeClass.pref_label == label).first()):
        msg = f"EType {label} was not found in db."
        raise RuntimeError(msg)

    _cache[label] = res

    return res


def _find_me_type_density(db, legacy_id: str, _cache: dict = {}) -> METypeDensity:
    if cached := _cache.get(legacy_id):
        return cached

    if not (res := db.query(METypeDensity).filter(ETypeClass.legacy_id == legacy_id).first()):
        msg = f"METypeDensity legacy id {legacy_id} was not found in db."
        raise RuntimeError(msg)

    _cache[legacy_id] = res

    return res


def _copy_fields(data: dict) -> dict:
    """Copy all fields except the hasPart entry."""
    return {k: v for k, v in data.items() if k != "hasPart"}


def _write_json(data: dict, path: Path) -> None:
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
