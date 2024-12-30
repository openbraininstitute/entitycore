from sqlalchemy import func
from app.models import (
    base,
)
import app.cli.curate as curate
def _find_by_legacy_id(legacy_id, db_type, db):
    use_func = func.instr
    if db.bind.dialect.name == "postgresql":
        use_func = func.strpos
    db_elem = (
        db.query(db_type).filter(use_func(db_type.legacy_id, legacy_id) > 0).first()
    )
    return db_elem

def get_or_create_brain_region(brain_region, db):
    brain_region = curate.curate_brain_region(brain_region)
    # Check if the brain region already exists in the database
    brain_region_at_id = brain_region["@id"].replace(
        "mba:", "http://api.brain-map.org/api/v2/data/Structure/"
    )
    br = (
        db.query(base.BrainRegion)
        .filter(base.BrainRegion.ontology_id == brain_region_at_id)
        .first()
    )
    if not br:
        # If not, create a new one
        br = base.BrainRegion(
            ontology_id=brain_region_at_id, name=brain_region["label"]
        )
        db.add(br)
        db.commit()
    return br.id


def get_or_create_species(species, db):
    # Check if the species already exists in the database
    sp = (
        db.query(base.Species)
        .filter(base.Species.taxonomy_id == species["@id"])
        .first()
    )
    if not sp:
        # If not, create a new one
        sp = base.Species(name=species["label"], taxonomy_id=species["@id"])
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
            brain_location = base.BrainLocation(x=x, y=y, z=z)
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
    li = db.query(base.License).filter(base.License.name == license["@id"]).first()
    if not li:
        raise ValueError(f"License {license} not found")
    return li.id


def get_or_create_strain(strain, species_id, db):
    # Check if the strain already exists in the database
    st = db.query(base.Strain).filter(base.Strain.taxonomy_id == strain["@id"]).first()
    if st:
        assert st.species_id == species_id

    if not st:
        # If not, create a new one
        st = base.Strain(
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
