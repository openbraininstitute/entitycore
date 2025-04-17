import datetime
import uuid
from datetime import timedelta
from typing import Any, Literal

import sqlalchemy as sa
from sqlalchemy import any_
from sqlalchemy.orm import Session

from app.cli import curate
from app.cli.mappings import STIMULUS_INFO
from app.db.model import (
    Agent,
    Asset,
    BrainRegion,
    Contribution,
    ElectricalRecordingStimulus,
    License,
    Role,
    Species,
    Strain,
    Subject,
)
from app.db.types import AssetStatus, EntityType, Sex
from app.logger import L
from app.schemas.base import ProjectContext
from app.utils.s3 import build_s3_path

AUTHORIZED_PUBLIC = True


def _find_by_legacy_id(legacy_id, db_type, db, _cache={}):
    if legacy_id in _cache:
        return _cache[legacy_id]

    res = db.query(db_type).filter(legacy_id == any_(db_type.legacy_id)).first()

    if res is not None:
        _cache[legacy_id] = res

    return res


def get_or_create_brain_region(brain_region, db, _cache=set()):
    brain_region = curate.curate_brain_region(brain_region)

    brain_region_id = int(brain_region["@id"])
    if brain_region_id in _cache:
        return brain_region_id

    br = db.query(BrainRegion).filter(BrainRegion.id == brain_region_id).first()

    if not br:
        br1 = db.query(BrainRegion).filter(BrainRegion.name == brain_region["label"]).first()
        if not br1:
            L.info("Replacing: {} -> failed", brain_region)
            return 997
        L.info("Replacing: {} -> {}", brain_region, br1.id)

        _cache.add(br1.id)
        return br1.id

    _cache.add(br.id)
    return br.id


def get_or_create_species(species, db, _cache={}):
    id_ = species["@id"]
    if id_ in _cache:
        return _cache[id_]

    # Check if the species already exists in the database
    sp = db.query(Species).filter(Species.taxonomy_id == id_).first()
    if not sp:
        # If not, create a new one
        sp = Species(name=species["label"], taxonomy_id=species["@id"])
        db.add(sp)
        db.commit()

    _cache[id_] = sp.id

    return sp.id


def create_stimulus(data, entity_id, project_context, db):
    label = data["label"]

    row = ElectricalRecordingStimulus(
        name=label,
        description=data.get("definition", None),
        dt=None,
        injection_type=STIMULUS_INFO[label]["type"],
        shape=STIMULUS_INFO[label]["shape"],
        start_time=None,
        end_time=None,
        recording_id=entity_id,
        authorized_public=AUTHORIZED_PUBLIC,
        authorized_project_id=project_context.project_id,
    )
    db.add(row)
    db.commit()


def get_brain_location_mixin(data, db):
    coordinates = data.get("brainLocation", {}).get("coordinatesInBrainAtlas", {})
    if coordinates is None:
        msg = "coordinates is None"
        raise RuntimeError(msg)

    brain_location = None
    if coordinates:
        x = coordinates.get("valueX", None)
        y = coordinates.get("valueY", None)
        z = coordinates.get("valueZ", None)
        if x is not None and y is not None and z is not None:
            brain_location = {"x": x, "y": y, "z": z}

    root = {
        "@id": "http://api.brain-map.org/api/v2/data/Structure/root",
        "label": "root",
    }

    brain_region = data.get("brainLocation", {}).get("brainRegion", root)

    if brain_region is None:
        msg = "brain_region is None"
        raise RuntimeError(msg)

    try:
        brain_region_id = get_or_create_brain_region(brain_region, db)
    except Exception:
        L.exception("data: {!r}", data)
        raise

    return brain_location, brain_region_id


def get_license_id(license, db, _cache={}):
    id_ = license["@id"]
    if id_ in _cache:
        return _cache[id_]

    # Check if the license already exists in the database
    li = db.query(License).filter(License.name == id_).first()
    if not li:
        msg = f"License {license} not found"
        raise ValueError(msg)

    _cache[id_] = li.id

    return li.id


def get_or_create_strain(strain, species_id, db, _cache={}):
    id_ = strain["@id"]
    if (species_id, id_) in _cache:
        return _cache[species_id, id_]

    # Check if the strain already exists in the database
    st = db.query(Strain).filter(Strain.taxonomy_id == id_).first()
    if st and st.species_id != species_id:
        msg = "st.species_id != species_id"
        raise RuntimeError(msg)

    if not st:
        # If not, create a new one
        st = Strain(
            name=strain["label"],
            taxonomy_id=strain["@id"],
            species_id=species_id,
        )
        db.add(st)
        db.commit()

    _cache[species_id, id_] = st.id

    return st.id


def get_species_mixin(data, db):
    species = data.get("subject", {}).get("species", {})
    if not species:
        msg = f"species is None: {data}"
        raise RuntimeError(msg)
    species_id = get_or_create_species(species, db)
    strain = data.get("subject", {}).get("strain", {})
    strain_id = None
    if strain:
        strain_id = get_or_create_strain(strain, species_id, db)
    return species_id, strain_id


def get_or_create_subject(data, project_context, db):
    species = data.get("subject", {}).get("species", {})
    if not species:
        msg = f"species is None: {data}"
        raise RuntimeError(msg)
    species_id = get_or_create_species(species, db)
    strain = data.get("subject", {}).get("strain", {})
    strain_id = None
    if strain:
        strain_id = get_or_create_strain(strain, species_id, db)

    age_fields = {}
    if age := data.get("subject", {}).get("age", {}):
        age_fields = curate_age(age)

    subject = Subject(
        name=data["name"],
        description=data["description"],
        species_id=species_id,
        strain_id=strain_id,
        sex=Sex.unknown,
        weight=None,
        age_value=age_fields.get("age_value", None),
        age_min=age_fields.get("age_min", None),
        age_max=age_fields.get("age_max", None),
        age_period=age_fields.get("age_period", None),
        authorized_project_id=project_context.project_id,
        authorized_public=AUTHORIZED_PUBLIC,
    )
    db.add(subject)
    db.commit()
    return subject.id


def curate_age(data):
    min_value = data.get("minValue", None)
    max_value = data.get("maxValue", None)
    unit = data.get("unitCode", None)
    period = data.get("period", None)
    value = data.get("value", None)

    value = timedelta(**{unit: value}) if value is not None else None
    min_value = timedelta(**{unit: min_value}) if min_value is not None else None
    max_value = timedelta(**{unit: max_value}) if max_value is not None else None

    if period.lower() == "post-natal":
        period = "postnatal"
    elif period.lower() == "pre-natal":
        period = "prenatal"
    else:
        msg = f"Unknown 'period' in Age: {data}"
        L.warning(msg)

    return {
        "age_value": value,
        "age_min": min_value,
        "age_max": max_value,
        "age_period": period,
    }


def get_license_mixin(data, db):
    license_id = None
    license = data.get("license", {})
    if license:
        license_id = get_license_id(license, db)
    return license_id


def get_agent_mixin(data, db):
    result = []
    for prop in ["_createdBy", "_updatedBy"]:
        legacy_id = data.get(prop, {})
        if not legacy_id:
            msg = f"legacy_id is None: {data}"
            raise RuntimeError(msg)
        agent_db = _find_by_legacy_id(legacy_id, Agent, db)
        if not agent_db:
            msg = f"legacy_id not found: {legacy_id}"
            raise RuntimeError(msg)
        result.append(agent_db.id)
    return result


def get_or_create_role(role_, db, _cache={}):
    # Check if the role already exists in the database
    role_ = curate.curate_role(role_)
    role_id = role_["@id"]

    if role_id in _cache:
        return _cache[role_id]

    r = db.query(Role).filter(Role.role_id == role_id).first()

    if not r:
        # If not, create a new one
        try:
            r = Role(role_id=role_["@id"], name=role_["label"])
            db.add(r)
            db.commit()
        except Exception:
            L.exception("Error creating role {}", role_)
            raise

    _cache[role_id] = r.id

    return r.id


def get_or_create_contribution(contribution_, entity_id, db):
    # Check if the Contribution already exists in the database
    if isinstance(contribution_, list):
        for c in contribution_:
            get_or_create_contribution(c, entity_id, db)
        return None

    agent_legacy_id = contribution_["agent"]["@id"]
    db_agent = _find_by_legacy_id(agent_legacy_id, Agent, db)
    if not db_agent:
        L.warning("Agent with legacy_id {} not found", agent_legacy_id)
        return None

    agent_id = db_agent.id
    role_ = contribution_.get("hadRole", {"@id": "unspecified", "label": "unspecified"})
    role_id = get_or_create_role(role_, db)
    c = (
        db.query(Contribution)
        .filter(
            Contribution.agent_id == agent_id,
            Contribution.role_id == role_id,
            Contribution.entity_id == entity_id,
        )
        .first()
    )
    if not c:
        # If not, create a new one
        c = Contribution(agent_id=agent_id, role_id=role_id, entity_id=entity_id)
        db.add(c)
        db.commit()
    return c.id


def import_contribution(data, db_item_id, db):
    contribution = data.get("contribution", [])
    contribution = curate.curate_contribution(contribution)
    if contribution:
        get_or_create_contribution(contribution, db_item_id, db)


def get_created_and_updated(data):
    return (
        datetime.datetime.fromisoformat(data["_createdAt"]),
        datetime.datetime.fromisoformat(data["_updatedAt"]),
    )


def get_or_create_distribution(
    distribution,
    entity_id: uuid.UUID,
    entity_type: str,
    db: Session,
    project_context: ProjectContext,
):
    # Check if the Distribution already exists in the database
    if isinstance(distribution, list):
        for c in distribution:
            get_or_create_distribution(c, entity_id, entity_type, db, project_context)
        return

    full_path = build_s3_path(
        vlab_id=project_context.virtual_lab_id,
        proj_id=project_context.project_id,
        entity_type=EntityType[entity_type],
        entity_id=entity_id,
        filename=distribution["name"],
        is_public=AUTHORIZED_PUBLIC,
    )
    query: sa.Select = sa.Select(Asset).where(Asset.full_path == full_path)
    row = db.execute(query).scalar_one_or_none()
    if row:
        if row.entity_id == entity_id:
            # Duplicated distribution
            return
        L.warning(
            "Conflicting distribution for ids {}, {}: {}", row.entity_id, entity_id, full_path
        )
        return
    asset = Asset(
        status=AssetStatus.CREATED,
        path=distribution["name"],
        full_path=full_path,
        is_directory=False,
        content_type=distribution["encodingFormat"],
        size=distribution["contentSize"]["value"],
        sha256_digest=bytes.fromhex(distribution["digest"]["value"]),
        meta={
            "legacy": distribution,  # for inspection
        },
        entity_id=entity_id,
    )
    db.add(asset)
    db.commit()


def import_distribution(data, db_item_id, db_item_type, db, project_context):
    distribution = data.get("distribution", [])
    distribution = curate.curate_distribution(distribution, project_context)
    if distribution:
        get_or_create_distribution(distribution, db_item_id, db_item_type, db, project_context)


def find_part_id(data: dict[str, Any], type_: Literal["NeuronMorphology", "EModel"]) -> str | None:
    has_part = data.get("hasPart")

    if not has_part:
        return None

    if isinstance(has_part, dict):
        return has_part.get("@id", None) if has_part.get("@type") == type_ else None

    if isinstance(has_part, list):
        for part in has_part:
            if isinstance(part, dict) and part.get("@type") == type_:
                return part.get("@id", None)

    return None
