import os
import sys
import argparse
import glob
import models.base as base
import models.morphology as morphology
import models.agent as agent
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm
import sqlalchemy
from sqlalchemy import func


# def get_or_create_contribution(contribution, db):
#     # Check if the contribution already exists in the database
#     c = (
#         db.query(base.Contribution)
#         .filter(
#             base.Contribution.agent_id == contribution["agent"]["@id"],
#             base.Contribution.role_id == contribution["role"]["@id"],
#             base.Contribution.entity_id == contribution["entity"]["@id"],
#         ).first()
#         )
#     if not c:
#     # If not, create a new one
#         c = base.Contribution(
#                 agent_id=contribution["agent"]["@id"],
#                 role_id=contribution["role"]["@id"],
#                 entity_id=contribution["entity"][" @id"])
#         db.add(c)
#         db.commit()
#     return c.id

def get_or_create_brain_region(brain_region, db):
    # Check if the brain region already exists in the database
    br = (
        db.query(base.BrainRegion)
        .filter(base.BrainRegion.ontology_id == brain_region["@id"])
        .first()
    )
    if not br:
        # If not, create a new one
        br = base.BrainRegion(
            ontology_id=brain_region["@id"], name=brain_region["label"]
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
        sp = base.Species(
            name=species["label"], taxonomy_id=species["@id"]
        )
        db.add(sp)
        db.commit()
    return sp.id

def get_or_create_license(license, db):
    # Check if the license already exists in the database
    li = (
        db.query(base.License)
        .filter(base.License.name == license["@id"])
        .first()
    )
    if not li:
        # If not, create a new one
        li = base.License(name=license["@id"])
        db.add(li)
        db.commit()
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

def import_agents(data_list, db):
    for data in data_list:
        if "Person" in data["@type"]:
            legacy_id = data["@id"]
            query_like = f'%{legacy_id}%'
            db_agent = db.query(agent.Person).filter(func.instr(agent.Agent.legacy_id, legacy_id) > 0).first()
            if not db_agent:
                try:
                    first_name=data["givenName"]
                    last_name=data["familyName"]
                    db_agent = db.query(agent.Person).filter(agent.Person.first_name == first_name,
                                                            agent.Person.last_name == last_name).first()
                    if db_agent:
                        l = db_agent.legacy_id.copy()
                        l.append(legacy_id)
                        db_agent.legacy_id = l
                         
                        db.commit()
                    else:
                        db_agent = agent.Person(
                            legacy_id=[legacy_id],
                            first_name=data["givenName"],
                            last_name=data["familyName"],
                        )
                        db.add(db_agent)
                        db.commit()
                except Exception as e:
                    print("Error importing person: ", data)
                    print(e)
                       

def import_morphologies(data_list, db):

    possible_data = [data for data in data_list if "ReconstructedNeuronMorphology" in data["@type"]]
    
    for data in tqdm(possible_data):
        legacy_id = data['@id']
        rm = db.query(morphology.ReconstructionMorphology).filter(morphology.ReconstructionMorphology.legacy_id == legacy_id).first()
        if not rm:
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
            # if not strain:
            #     print("Skipping reconstruction morphology due to missing strain.")
            #     continue
            strain_id = None
            if strain:
                strain_id = get_or_create_strain(strain, species_id, db)
            brain_location = None
            coordinates = data.get("brainLocation", {}).get("coordinatesInBrainAtlas", {})
            if coordinates:
                x = coordinates.get("valueX", None)
                y = coordinates.get("valueY", None)
                z = coordinates.get("valueZ", None)
                if x is not None and y is not None and z is not None:
                    brain_location = base.BrainLocation(x=x,y=y, z=z)
            license = data.get("license", {})
            license_id = None
            if license:
                license_id = get_or_create_license(license, db)

            # contribution_id = None
            # contribution = data.get("contribution", {})
            # if contribution:
            #     contribution_id = get_or_create_contribution(contribution, db)
            db_reconstruction_morphology = morphology.ReconstructionMorphology(
                legacy_id=data.get("@id", None),
                name=name,
                description=description,
                brain_location=brain_location,
                brain_region_id=brain_region_id,
                species_id=species_id,
                strain_id=strain_id,
                license_id=license_id,
                # contribution_id=contribution_id,
            )
            db.add(db_reconstruction_morphology)
            db.commit()
            db.refresh(db_reconstruction_morphology)


def import_morphology_feature_annotations(data_list, db):
    possible_data = [data for data in data_list if "NeuronMorphologyFeatureAnnotation" in data["@type"]]
    for data in tqdm(possible_data):
        try:
            legacy_id = data.get('hasTarget',{}).get('hasSource',{}).get('@id', None)
            if not legacy_id:
                print("Skipping morphology feature annotation due to missing legacy id.")
                continue
            rm = db.query(morphology.ReconstructionMorphology).filter(morphology.ReconstructionMorphology.legacy_id == legacy_id).first()
            if not rm:
                print("skipping morphology that is not imported")
                continue
            all_measurements = [] 
            for measurement in data.get('hasBody', []):
                serie = measurement.get('value', {}).get('series', [])
                if type(serie) == dict:
                    serie = [serie]
                measurement_serie = [
                    morphology.MorphologyMeasurementSerieElement(
                        name=serie_elem.get('statistic', None),
                        value=serie_elem.get('value', None),
                        )
                        for serie_elem in serie
                ]

                all_measurements.append(
                    morphology.MorphologyMeasurement(
                        measurement_of=measurement.get('isMeasurementOf', {}).get('label', None),
                        measurement_serie = measurement_serie)
                )
                
            db_morphology_feature_annotation = morphology.MorphologyFeatureAnnotation(
                reconstruction_morphology_id=rm.id)
            db_morphology_feature_annotation.measurements = all_measurements
            db.add(db_morphology_feature_annotation)
            db.commit()
            db.refresh(db_morphology_feature_annotation)
        except sqlalchemy.exc.IntegrityError:
            # todo: investigate if what is actually happening
            print('2 annotations for a morphology ignoring')
            db.rollback()
            continue 
        except Exception as e:
            print(f"Error: {e}")
            import ipdb; ipdb.set_trace()
            print(data)
            
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
        with open(file_path, "r") as f:
            data = json.load(f)
            import_agents(data, db)
    
    # for file_path in all_files:
    #     print(file_path)
    #     with open(file_path, "r") as f:
    #         data = json.load(f)
    #         import_morphologies(data, db)
    # for file_path in all_files:
    #     print(file_path)
    #     with open(file_path, "r") as f:
    #         data = json.load(f)
    #         import_morphology_feature_annotations(data, db)



if __name__ == "__main__":
    main()
