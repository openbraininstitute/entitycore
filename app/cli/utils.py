import datetime
import uuid
from typing import Any, Literal

import sqlalchemy as sa
from sqlalchemy import any_
from sqlalchemy.orm import Session

from app.cli import curate
from app.config import settings
from app.db.model import (
    Agent,
    Asset,
    BrainRegion,
    Contribution,
    Ion,
    IonChannelAssociation,
    IonChannelModel,
    License,
    Role,
    Species,
    Strain,
)
from app.db.types import AssetStatus, EntityType
from app.logger import L
from app.schemas.base import ProjectContext
from app.schemas.ion_channel_model import NmodlParameters
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

    bucket_name = settings.S3_BUCKET_NAME
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
        bucket_name=bucket_name,
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


def ensurelist(x):
    return x if isinstance(x, list) else [x]


def find_id_in_entity(entity: dict | None, type_: str, entity_list_key: str):
    if not entity:
        return None
    return next(
        (
            part.get("@id")
            for part in ensurelist(entity.get(entity_list_key, []))
            if is_type(part, type_)
        ),
        None,
    )


def is_type(data: dict, type_: str):
    return type_ in ensurelist(data.get("@type", []))


def import_distribution(
    data: dict,
    db_item_id: uuid.UUID,
    db_item_type: EntityType,
    db: Session,
    project_context: ProjectContext,
):
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


def get_or_create_ion(ion: dict[str, Any], db: Session, _cache=set()):
    label = ion["label"]
    if label in _cache:
        return _cache[label]

    q = sa.select(Ion).where(Ion.name == label)
    db_ion = db.execute(q).scalar_one_or_none() or Ion(name=ion.get("label"))
    db.flush()

    _cache.set(db_ion.id)

    return db_ion.id


def import_ion_channel_models(
    emodel_config: dict,
    emodel_id: uuid.UUID,
    all_data_by_id: dict[str, dict[str, Any]],
    db: Session,
):
    subcellular_model_script_ids = [
        script["@id"]
        for script in emodel_config.get("uses") or []
        if is_type(script, "SubCellularModelScript")
    ]

    ion_channel_models: list[tuple[dict[str, Any], uuid.UUID]] = []

    for id_ in subcellular_model_script_ids:
        if (script := all_data_by_id.get(id_)) and (ion := script.get("ion")):
            temperature = script.get("temperature", {})
            temp_unit = str(temperature.get("unitCode", "")).lower()

            assert temp_unit == "c"  # noqa: S101

            temperature_value = temperature.get("value")

            nmodl_parameters: dict[str, Any] | None = script.get("nmodlParameters")
            nmodl_parameters_validated: NmodlParameters | None = None
            if nmodl_parameters:
                range_ = nmodl_parameters.get("range")
                read = nmodl_parameters.get("read")
                useion = nmodl_parameters.get("useion")
                write = nmodl_parameters.get("write")
                nonspecific = nmodl_parameters.get("nonspecific")

                d = {
                    **nmodl_parameters,
                    "range": range_ and ensurelist(range_),
                    "read": read and ensurelist(read),
                    "useion": useion and ensurelist(useion),
                    "write": write and ensurelist(write),
                    "nonspecific": nonspecific and ensurelist(nonspecific),
                }

                nmodl_parameters_validated = NmodlParameters.model_validate(d)

            if nmodl_parameters_validated is None:
                print("None value")

            db_ion_channel_model = IonChannelModel(
                name=script["name"],
                description=script.get("descripton", ""),
                identifier=script.get("identifier", ""),
                modelId=script.get("modelId", ""),
                is_ljp_corrected=script.get("isLjpCorrected", False),
                is_temperature_dependent=script.get("isTemperatureDependent", False),
                temperature_celsius=int(temperature_value),
                nmodl_parameters=nmodl_parameters_validated.model_dump()
                if nmodl_parameters_validated is not None
                else None,
                emodel_id=emodel_id,
            )

            db.add(db_ion_channel_model)

            db.flush()

            ion_associations = [
                IonChannelAssociation(
                    ion_id=db_ion_id, ion_channel_model_id=db_ion_channel_model.id
                )
                for db_ion_id in [get_or_create_ion(ion, db) for ion in ensurelist(ion)]
            ]

            db.add_all(ion_associations)

            db.flush()

            ion_channel_models.append((script, db_ion_channel_model.id))

    return ion_channel_models
