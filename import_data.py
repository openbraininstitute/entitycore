import os
import sys
import argparse
import glob
import model
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm


def get_or_create_brain_region(brain_region, db):
    # Check if the brain region already exists in the database
    br = (
        db.query(model.BrainRegion)
        .filter(model.BrainRegion.ontology_id == brain_region["@id"])
        .first()
    )
    if not br:
        # If not, create a new one
        br = model.BrainRegion(
            ontology_id=brain_region["@id"], name=brain_region["label"]
        )
        db.add(br)
        db.commit()
    return br.id


def get_or_create_species(species, db):
    # Check if the species already exists in the database
    sp = (
        db.query(model.Species)
        .filter(model.Species.taxonomy_id == species["@id"])
        .first()
    )
    if not sp:
        # If not, create a new one
        sp = model.Species(
            Name=species["label"], taxonomy_id=species["@id"]
        )
        db.add(sp)
        db.commit()
    return sp.id


def get_or_create_strain(strain, species_id, db):
    # Check if the strain already exists in the database
    st = db.query(model.Strain).filter(model.Strain.taxonomy_id == strain["@id"]).first()
    if st:
        assert st.species_id == species_id

    if not st:
        # If not, create a new one
        st = model.Strain(
            Name=strain["label"],
            taxonomy_id=strain["@id"],
            species_id=species_id,
        )
        db.add(st)
        db.commit()
    return st.id


def import_morphologies(data_list, db):

    possible_data = [data for data in data_list if "ReconstructedNeuronMorphology" in data["@type"]]
    
    for data in tqdm(possible_data):
        if "ReconstructedNeuronMorphology" in data["@type"]:
            brain_location = data.get("brainLocation", None)
            if not brain_location:
                print(
                    "Skipping reconstruction morphology due to missing brain location."
                )
                continue
            brain_region = brain_location.get("brainRegion", None)
            if not brain_region:
                print("Skipping reconstruction morphology due to missing brain region.")
                continue
            brain_region_id = get_or_create_brain_region(brain_region, db)
            description = data.get("description", None)
            name = data.get("name", None)
            species = data.get("subject", {}).get("species", {})
            if not species:
                print("Skipping reconstruction morphology due to missing species.")
            species_id = get_or_create_species(species, db)
            strain = data.get("subject", {}).get("strain", {})
            if not strain:
                print("Skipping reconstruction morphology due to missing strain.")
                continue
            strain_id = get_or_create_strain(strain, species_id, db)
            brain_location = None
            coordinates = data.get("subject", {}).get("coordinatesInBrainAtlas", {})
            if coordinates:
                x = coordinates.get("valueX", None)
                y = coordinates.get("valueY", None)
                z = coordinates.get("valueZ", None)
                if x and y and z:
                    brain_location = model.BrainLocation(x, y, z)
                
            db_reconstruction_morphology = model.ReconstructionMorphology(
                name=name,
                description=description,
                brain_location=brain_location,
                brain_region_id=brain_region_id,
                species_id=species_id,
                strain_id=strain_id,
            )
            db.add(db_reconstruction_morphology)
            db.commit()
            db.refresh(db_reconstruction_morphology)


def main():
    parser = argparse.ArgumentParser(description="Import data script")
    parser.add_argument("--db", required=True, help="Database parameter")
    parser.add_argument("--input_dir", required=True, help="Input directory path")

    args = parser.parse_args()

    if not os.path.exists(args.input_dir):
        print(f"Error: Input directory '{args.input_dir}' does not exist")
        sys.exit(1)

    if not os.path.exists(args.db):
        print(f"Error: Database file '{args.db}' does not exist")
        sys.exit(1)

    engine = create_engine(
        "sqlite:///" + args.db, connect_args={"check_same_thread": False}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    all_files = glob.glob(os.path.join(args.input_dir, "*", "*", "*.json"))
    for file_path in all_files:
        print(file_path)
        with open(file_path, "r") as f:
            data = json.load(f)
            import_morphologies(data, db)



if __name__ == "__main__":
    main()
