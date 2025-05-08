import datetime
import uuid
from datetime import timedelta
from typing import Any, Literal

import sqlalchemy as sa
from sqlalchemy import and_, any_
from sqlalchemy.orm import Session

from app.cli import curate
from app.cli.mappings import (
    MEASUREMENT_STATISTIC_MAP,
    MEASUREMENT_UNIT_MAP,
    STIMULUS_INFO,
    STRUCTURAL_DOMAIN_MAP,
)
from app.db.model import (
    Agent,
    Asset,
    BrainRegion,
    BrainRegionHierarchyName,
    Contribution,
    ElectricalRecordingStimulus,
    Ion,
    IonChannelModel,
    IonChannelModelToEModel,
    License,
    MeasurementItem,
    MeasurementKind,
    MTypeClass,
    Role,
    Species,
    Strain,
    Subject,
    SynapticPathway,
)
from app.db.types import AssetStatus, EntityType, Sex
from app.logger import L
from app.schemas.base import ProjectContext
from app.schemas.ion_channel_model import NeuronBlock
from app.utils.s3 import build_s3_path

AUTHORIZED_PUBLIC = True


def ensurelist(x):
    return x if isinstance(x, list) else [x]


def _find_by_legacy_id(legacy_id, db_type, db, _cache={}):
    if legacy_id in _cache:
        return _cache[legacy_id]

    res = db.query(db_type).filter(legacy_id == any_(db_type.legacy_id)).first()

    if res is not None:
        _cache[legacy_id] = res

    return res


def get_brain_region_by_hier_id(brain_region, hierarchy_name, db, _cache={}):
    brain_region = curate.curate_brain_region(brain_region)

    brain_region_id = int(brain_region["@id"])
    if (hierarchy_name, brain_region_id) in _cache:
        return _cache[hierarchy_name, brain_region_id]

    br = db.execute(
        sa.select(BrainRegion)
        .join(
            BrainRegionHierarchyName, BrainRegion.hierarchy_name_id == BrainRegionHierarchyName.id
        )
        .where(
            BrainRegionHierarchyName.name == hierarchy_name,
            BrainRegion.hierarchy_id == brain_region_id,
        )
    ).scalar_one_or_none()

    if br is None:
        msg = f"({hierarchy_name}, {brain_region}) not found in database"
        raise RuntimeError(msg)

    _cache[hierarchy_name, brain_region_id] = br.id
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

    info = STIMULUS_INFO[label]

    row = ElectricalRecordingStimulus(
        name=info["ecode"],
        description=data.get("definition", None),
        dt=None,
        injection_type=info["type"],
        shape=info["shape"],
        start_time=None,
        end_time=None,
        recording_id=entity_id,
        authorized_public=AUTHORIZED_PUBLIC,
        authorized_project_id=project_context.project_id,
    )
    db.add(row)
    db.commit()


def get_brain_location(data):
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

    return brain_location


def get_brain_region(data, hierarchy_name, db):
    root = {
        "@id": "http://api.brain-map.org/api/v2/data/Structure/root",
        "label": "root",
    }

    brain_region = data.get("brainLocation", {}).get("brainRegion", root)

    if brain_region is None:
        msg = "brain_region is None"
        raise RuntimeError(msg)

    brain_region_id = get_brain_region_by_hier_id(brain_region, hierarchy_name, db)

    return brain_region_id


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


def get_or_create_ion(ion: dict[str, Any], db: Session, _cache={}):
    label = ion["label"]
    if label in _cache:
        return _cache[label]

    ontology_id = ion.get("@id")

    q = sa.select(Ion).where(Ion.name == label.lower())
    db_ion = db.execute(q).scalar_one_or_none()
    if not db_ion:
        db_ion = Ion(name=ion.get("label"), ontology_id=ontology_id)
        db.add(db_ion)
        db.flush()

    _cache[label] = db_ion

    return db_ion


def import_ion_channel_model(
    script: dict[str, Any], project_context: ProjectContext, hierarchy_name, db: Session
):
    legacy_id = script["@id"]
    legacy_self = script["_self"]
    temperature = script.get("temperature", {})
    temp_unit = str(temperature.get("unitCode", "")).lower()

    assert temp_unit == "c"
    temperature_value = temperature.get("value")

    neuron_block_raw: dict[str, Any] | None = script.get("nmodlParameters")
    exposed_parameter_raw: list[dict[str, Any]] | None = script.get("exposesParameter")
    neuron_block_validated: NeuronBlock | None = None

    exposed_parameter_unit = {}
    nonspecific_unit = {}
    if exposed_parameter_raw:
        for param in ensurelist(exposed_parameter_raw):
            if param.get("ionName") == "non-specific":
                name = param.get("name")
                unit = param.get("unitCode") or param.get("unit")
                nonspecific_unit[name] = unit
            else:
                name = param.get("name")
                unit = param.get("unitCode") or param.get("unit")
                exposed_parameter_unit[name] = unit

    read_raw = ensurelist((neuron_block_raw or {}).get("read", []))
    write_raw = ensurelist((neuron_block_raw or {}).get("write", []))

    if neuron_block_raw:
        useion = ensurelist(neuron_block_raw.get("useion", []))
        ion_entries = ensurelist(script.get("ion", []))
        useion_structured = []

        for useion_name in useion:
            # Define valid variable names for this ion
            valid_read_vars = {
                f"e{useion_name}",
                f"{useion_name}i",
                f"{useion_name}o",
                f"d{useion_name}",
            }
            valid_write_vars = {f"i{useion_name}", f"{useion_name}i", f"{useion_name}o"}

            read = [var for var in read_raw if var in valid_read_vars]
            write = [var for var in write_raw if var in valid_write_vars]

            if useion_name.lower() not in (
                (entry.get("label", "").lower() if entry else "")
                for entry in ensurelist(script.get("ion"))
            ):
                ion = {"@id": None, "label": useion_name}
            else:
                ion = next(
                    entry
                    for entry in ion_entries
                    if entry.get("label", "").lower() == useion_name.lower()
                )

            useion_structured.append(
                {
                    "ion_name": get_or_create_ion(ion, db).name,
                    "read": read,
                    "write": write,
                    "valence": neuron_block_raw.get("valence"),
                    "main_ion": True if len(useion) == 1 else None,
                }
            )

        range_raw = ensurelist(neuron_block_raw.get("range", []))
        range_list = [{name: exposed_parameter_unit.get(name)} for name in range_raw]

        nonspecific = []
        for key, value in nonspecific_unit.items():
            nonspecific.append({key: value})

        neuron_block_dict = {
            "range": range_list,
            "global": [],
            "nonspecific": nonspecific,
            "useion": useion_structured,
        }
        neuron_block_validated = NeuronBlock.model_validate(neuron_block_dict)

    brain_region_id = get_brain_region(script, hierarchy_name, db)
    species_id, strain_id = get_species_mixin(script, db)
    created_at, updated_at = get_created_and_updated(script)

    assert neuron_block_validated

    db_ion_channel_model = IonChannelModel(
        legacy_id=[legacy_id],
        legacy_self=[legacy_self],
        name=script["name"],
        nmodl_suffix=script.get("suffix")
        or (neuron_block_raw.get("suffix") if neuron_block_raw else ""),
        description=script.get("description", ""),
        is_ljp_corrected=script.get("isLjpCorrected", False),
        is_temperature_dependent=script.get("isTemperatureDependent", False),
        temperature_celsius=int(temperature_value),
        neuron_block=neuron_block_validated.model_dump(
            by_alias=True
        ),  # global instead of global_ in the output dict
        brain_region_id=brain_region_id,
        species_id=species_id,
        strain_id=strain_id,
        creation_date=created_at,
        update_date=updated_at,
        authorized_project_id=project_context.project_id,
        authorized_public=AUTHORIZED_PUBLIC,
        is_stochastic=script.get("name", "").lower().startswith("stoch"),
    )

    db.add(db_ion_channel_model)
    db.flush()

    import_contribution(script, db_ion_channel_model.id, db)
    import_distribution(
        script, db_ion_channel_model.id, EntityType.ion_channel_model, db, project_context
    )

    return db_ion_channel_model


def import_ion_channel_models(
    emodel_config: dict,
    emodel_id: uuid.UUID,
    all_data_by_id: dict[str, dict[str, Any]],
    project_context: ProjectContext,
    hierarchy_name: str,
    db: Session,
):
    subcellular_model_script_ids = [
        script["@id"]
        for script in emodel_config.get("uses") or []
        if is_type(script, "SubCellularModelScript")
    ]

    ion_channel_model_ids: list[uuid.UUID] = []

    for id_ in subcellular_model_script_ids:
        script = all_data_by_id.get(id_) or {}

        legacy_id = script["@id"]

        db_ion_channel_model = _find_by_legacy_id(legacy_id, IonChannelModel, db)

        if db_ion_channel_model:
            ion_channel_model_ids.append(db_ion_channel_model.id)
            continue

        db_ion_channel_model = import_ion_channel_model(script, project_context, hierarchy_name, db)

        ion_channel_model_ids.append(db_ion_channel_model.id)

        db.flush()

    icm_associations = [
        IonChannelModelToEModel(ion_channel_model_id=icm_id, emodel_id=emodel_id)
        for icm_id in ion_channel_model_ids
    ]

    db.add_all(icm_associations)

    db.flush()


def _get_pathway_info(data, hierarchy_name, db):  # noqa: C901
    pre_region_id = pre_mtype_label = post_region_id = post_mtype_label = None

    for entry in data["preSynaptic"]:
        if "BrainRegion" in entry["about"]:
            pre_region_id = get_brain_region_by_hier_id(entry, hierarchy_name, db)
        elif "mtypes" in entry["@id"] or "BrainCell:Type" in entry["about"]:
            pre_mtype_label = entry["label"]

    for entry in data["postSynaptic"]:
        if "BrainRegion" in entry["about"]:
            post_region_id = get_brain_region_by_hier_id(entry, hierarchy_name, db)
        elif "mtypes" in entry["@id"] or "BrainCell:Type" in entry["about"]:
            post_mtype_label = entry["label"]

    if not all([pre_region_id, post_region_id, pre_mtype_label, post_mtype_label]):
        msg = f"Failed to find pre/post synaptic information for {data}"
        raise RuntimeError(msg)

    msg = ""
    pre_mtype = db.query(MTypeClass).filter(MTypeClass.pref_label == pre_mtype_label).first()

    if not pre_mtype:
        msg += f"mtype {pre_mtype_label} is not present in the database.\n"

    post_mtype = db.query(MTypeClass).filter(MTypeClass.pref_label == post_mtype_label).first()
    if not post_mtype:
        msg += f"mtype {post_mtype_label} is not present in the database.\n"

    if msg:
        raise RuntimeError(msg)

    return pre_mtype.id, post_mtype.id, pre_region_id, post_region_id  # pyright: ignore [reportPossiblyUnboundVariable]


def get_or_create_synaptic_pathway(data, project_context, hierarchy_name, db):
    pre_mtype_id, post_mtype_id, pre_region_id, post_region_id = _get_pathway_info(
        data, hierarchy_name, db
    )

    res = (
        db.query(SynapticPathway)
        .where(
            and_(
                SynapticPathway.pre_mtype_id == pre_mtype_id,
                SynapticPathway.post_mtype_id == post_mtype_id,
                SynapticPathway.pre_region_id == pre_region_id,
                SynapticPathway.post_region_id == post_region_id,
            )
        )
        .first()
    )

    if not res:
        res = SynapticPathway(
            pre_mtype_id=pre_mtype_id,
            post_mtype_id=post_mtype_id,
            pre_region_id=pre_region_id,
            post_region_id=post_region_id,
            authorized_project_id=project_context.project_id,
        )
        db.add(res)
        db.commit()

    return res.id


def get_or_create_subject(data, project_context, db):
    subject = data.get("subject", {})

    species = subject.get("species", {})
    if not species:
        msg = f"species is None: {data}"
        raise RuntimeError(msg)
    species_id = get_or_create_species(species, db)
    strain = subject.get("strain", {})
    strain_id = None
    if strain:
        strain_id = get_or_create_strain(strain, species_id, db)

    age_fields = {}
    if age := subject.get("age", {}):
        age_fields = curate_age(age)

    subject = Subject(
        name=subject.get("name", "Unknown"),
        description=subject.get("description", ""),
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


def to_pref_label(s):
    return s.replace(" ", "_").lower()


def build_measurement_item(item):
    if (statistic := item.get("statistic")) is None:
        # L.debug("measurement item has no statistic: {}", item)
        return None
    if (unit := item.get("unitCode")) is None:
        # L.debug("measurement item has no unit: {}", item)
        return None
    if (value := item.get("value")) is None:
        # L.debug("measurement item has no value: {}", item)
        return None
    return MeasurementItem(
        name=MEASUREMENT_STATISTIC_MAP[statistic],
        unit=MEASUREMENT_UNIT_MAP[unit],
        value=value,
    )


def build_measurement_kind(measurement, measurement_items):
    if not measurement_items:
        # L.debug("measurement has no items")
        return None
    measurement_meta = measurement.get("isMeasurementOf", {})
    definition = measurement_meta.get("label")
    pref_label = measurement_meta.get("prefLabel") or to_pref_label(definition)
    return MeasurementKind(
        pref_label=pref_label,
        structural_domain=STRUCTURAL_DOMAIN_MAP[measurement.get("compartment")],
        measurement_items=measurement_items,
    )
