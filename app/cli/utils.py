from sqlalchemy import func

import app.cli.curate as curate
from app.db.model import (
    Agent,
    BrainLocation,
    BrainRegion,
    Contribution,
    License,
    Role,
    Species,
    Strain,
)


def _find_by_legacy_id(legacy_id, db_type, db):
    db_elem = (
        db.query(db_type).filter(func.strpos(db_type.legacy_id, legacy_id) > 0).first()
    )
    return db_elem


def get_or_create_brain_region(brain_region, db):
    brain_region = curate.curate_brain_region(brain_region)
    # Check if the brain region already exists in the database
    brain_region_at_id = brain_region["@id"].replace(
        "mba:", "http://api.brain-map.org/api/v2/data/Structure/"
    )
    br = (
        db.query(BrainRegion)
        .filter(BrainRegion.ontology_id == brain_region_at_id)
        .first()
    )
    if not br:
        # If not, create a new one
        br = BrainRegion(
            ontology_id=brain_region_at_id, name=brain_region["label"]
        )
        db.add(br)
        db.commit()
    return br.id


def get_or_create_species(species, db):
    # Check if the species already exists in the database
    sp = (
        db.query(Species)
        .filter(Species.taxonomy_id == species["@id"])
        .first()
    )
    if not sp:
        # If not, create a new one
        sp = Species(name=species["label"], taxonomy_id=species["@id"])
        db.add(sp)
        db.commit()
    return sp.id


def get_brain_location_mixin(data, db):
    coordinates = data.get("brainLocation", {}).get("coordinatesInBrainAtlas", {})
    assert coordinates is not None, "coordinates is None"
    brain_location = None
    if coordinates:
        x = coordinates.get("valueX", None)
        y = coordinates.get("valueY", None)
        z = coordinates.get("valueZ", None)
        if x is not None and y is not None and z is not None:
            brain_location = BrainLocation(x=x, y=y, z=z)
    root = {
        "@id": "http://api.brain-map.org/api/v2/data/Structure/root",
        "label": "root",
    }
    brain_region = data.get("brainLocation", {}).get("brainRegion", root)
    assert brain_region is not None, "brain_region is None"
    try:
        brain_region_id = get_or_create_brain_region(brain_region, db)
    except Exception as e:
        print(data)
        raise (e)
    return brain_location, brain_region_id


def get_license_id(license, db):
    # Check if the license already exists in the database
    li = db.query(License).filter(License.name == license["@id"]).first()
    if not li:
        raise ValueError(f"License {license} not found")
    return li.id


def get_or_create_strain(strain, species_id, db):
    # Check if the strain already exists in the database
    st = db.query(Strain).filter(Strain.taxonomy_id == strain["@id"]).first()
    if st:
        assert st.species_id == species_id

    if not st:
        # If not, create a new one
        st = Strain(
            name=strain["label"],
            taxonomy_id=strain["@id"],
            species_id=species_id,
        )
        db.add(st)
        db.commit()
    return st.id


def get_species_mixin(data, db):
    species = data.get("subject", {}).get("species", {})
    assert species, "species is None: {}".format(data)
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
    for property in ["_createdBy", "_updatedBy"]:
        legacy_id = data.get(property, {})
        assert legacy_id, "legacy_id is None: {}".format(data)
        agent_db = _find_by_legacy_id(legacy_id, Agent, db)
        assert agent_db, "legacy_id not found: {}".format(legacy_id)
        result.append(agent_db.id)
    return result


def get_or_create_role(role_, db):
    # Check if the role already exists in the database
    role_ = curate.curate_role(role_)
    r = db.query(Role).filter(Role.role_id == role_["@id"]).first()
    if not r:
        # If not, create a new one
        try:
            r = Role(role_id=role_["@id"], name=role_["label"])
            db.add(r)
            db.commit()
        except Exception as e:
            print(e)
            print(f"Error creating role {role_}")
            raise e
    return r.id


def get_or_create_contribution(contribution_, entity_id, db):
    # Check if the Contribution already exists in the database
    if type(contribution_) is list:
        for c in contribution_:
            get_or_create_contribution(c, entity_id, db)
        return None
    agent_legacy_id = contribution_["agent"]["@id"]
    db_agent = _find_by_legacy_id(agent_legacy_id, Agent, db)
    if not db_agent:
        print(f"Agent with legacy_id {agent_legacy_id} not found")
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
        c = Contribution(
            agent_id=agent_id, role_id=role_id, entity_id=entity_id
        )
        db.add(c)
        db.commit()
    return c.id


def import_contribution(data, db_item_id, db):
    contribution = data.get("contribution", [])
    contribution = curate.curate_contribution(contribution)
    if contribution:
        get_or_create_contribution(contribution, db_item_id, db)
