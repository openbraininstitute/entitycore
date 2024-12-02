import os
import sys
import argparse
import glob
import models.base as base
import models.morphology as morphology
import models.agent as agent
import models.role as role
import models.contribution as contribution
import models.annotation as annotation
import models.density as density
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm
import sqlalchemy
from sqlalchemy import func
import curate_data as curate


def get_agent_from_legacy_id(legacy_id, db):
    db_agent = (
        db.query(agent.Agent)
        .filter(func.instr(agent.Agent.legacy_id, legacy_id) > 0)
        .first()
    )
    return db_agent


def get_or_create_role(role_, db):
    # Check if the role already exists in the database
    role_ = curate.curate_role(role_)
    r = db.query(role.Role).filter(role.Role.role_id == role_["@id"]).first()
    if not r:
        # If not, create a new one
        try:
            r = role.Role(role_id=role_["@id"], name=role_["label"])
            db.add(r)
            db.commit()
        except Exception as e:
            print(e)
            print(f"Error creating role {role_}")
            raise e
    return r.id


def get_or_create_annotation_body(annotation_body, db):
    annotation_body = curate.curate_annotation_body(annotation_body)
    if "DataMaturity" in annotation_body["@type"]:
        ab = (
            db.query(annotation.DataMaturityAnnotationBody)
            .filter(
                annotation.DataMaturityAnnotationBody.label == annotation_body["label"]
            )
            .first()
        )
        if not ab:
            ab = annotation.DataMaturityAnnotationBody(label=annotation_body["label"])
            db.add(ab)
            db.commit()
        return ab.id
    if "MType" in annotation_body["@type"]:
        ab = (
            db.query(annotation.MTypeAnnotationBody)
            .filter(annotation.MTypeAnnotationBody.label == annotation_body["label"])
            .first()
        )
        if not ab:
            ab = annotation.MTypeAnnotationBody(label=annotation_body["label"])
            db.add(ab)
            db.commit()
        return ab.id
    assert False, f"Unknown annotation body type {annotation_body['@type']}"


def get_or_create_contribution(contribution_, entity_id, db):
    # Check if the contribution already exists in the database
    if type(contribution_) is list:
        for c in contribution_:
            get_or_create_contribution(c, entity_id, db)
        return
    agent_legacy_id = contribution_["agent"]["@id"]
    db_agent = get_agent_from_legacy_id(agent_legacy_id, db)
    if not db_agent:
        print(f"Agent with legacy_id {agent_legacy_id} not found")
        return
    agent_id = db_agent.id
    role_ = contribution_.get("hadRole", {"@id": "unspecified", "label": "unspecified"})
    role_id = get_or_create_role(role_, db)
    c = (
        db.query(contribution.Contribution)
        .filter(
            contribution.Contribution.agent_id == agent_id,
            contribution.Contribution.role_id == role_id,
            contribution.Contribution.entity_id == entity_id,
        )
        .first()
    )
    if not c:
        # If not, create a new one
        c = contribution.Contribution(
            agent_id=agent_id, role_id=role_id, entity_id=entity_id
        )
        db.add(c)
        db.commit()
    return c.id


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
        sp = base.Species(name=species["label"], taxonomy_id=species["@id"])
        db.add(sp)
        db.commit()
    return sp.id


def get_or_create_license(license, db):
    # Check if the license already exists in the database
    li = db.query(base.License).filter(base.License.name == license["@id"]).first()
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
            db_agent = (
                db.query(agent.Person)
                .filter(func.instr(agent.Agent.legacy_id, legacy_id) > 0)
                .first()
            )
            if not db_agent:
                try:
                    data = curate.curate_person(data)
                    first_name = data["givenName"]
                    last_name = data["familyName"]
                    db_agent = (
                        db.query(agent.Person)
                        .filter(
                            agent.Person.first_name == first_name,
                            agent.Person.last_name == last_name,
                        )
                        .first()
                    )
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
        elif "Organization" in data["@type"]:
            legacy_id = data["@id"]
            db_agent = (
                db.query(agent.Organization)
                .filter(func.instr(agent.Agent.legacy_id, legacy_id) > 0)
                .first()
            )
            if not db_agent:
                try:
                    name = data["name"]
                    db_agent = (
                        db.query(agent.Organization)
                        .filter(agent.Organization.name == name)
                        .first()
                    )
                    if db_agent:
                        l = db_agent.legacy_id.copy()
                        l.append(legacy_id)
                        db_agent.legacy_id = l

                        db.commit()
                    else:
                        db_agent = agent.Organization(
                            legacy_id=[legacy_id],
                            name=data["name"],
                            label=data.get("label", ""),
                            alternative_name=data.get("alternativeName", ""),
                        )
                        db.add(db_agent)
                        db.commit()
                except Exception as e:
                    print("Error importing organization: ", data)
                    print(e)


def get_or_create_morphology_annotation(annotation_, reconstruction_morphology_id, db):
    db_annotation = annotation.Annotation(
        entity_id=reconstruction_morphology_id,
        note=annotation_.get("note", None),
        annotation_body_id=get_or_create_annotation_body(annotation_["hasBody"], db),
    )
    db.add(db_annotation)
    db.commit()
    return db_annotation.id

def get_brain_location_mixin(data, db):
    coordinates = data.get("brainLocation", {}).get(
        "coordinatesInBrainAtlas", {}
    )
    assert coordinates is not None, "coordinates is None"
    brain_location = None
    if coordinates:
        x = coordinates.get("valueX", None)
        y = coordinates.get("valueY", None)
        z = coordinates.get("valueZ", None)
        if x is not None and y is not None and z is not None:
            brain_location = base.BrainLocation(x=x, y=y, z=z)
    brain_region = data.get("brainLocation", {}).get("brainRegion", None)
    assert brain_region is not None, "brain_region is None"
    brain_region_id = get_or_create_brain_region(brain_region, db)
    return brain_location, brain_region_id 

def get_species_mixin(data, db):
    species = data.get("subject", {}).get("species", {})
    assert species , "species is None"
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
        license_id = get_or_create_license(license, db)
    return license_id

def import_morphologies(data_list, db):

    possible_data = [
        data for data in data_list if "ReconstructedNeuronMorphology" in data["@type"]
    ]

    for data in tqdm(possible_data):
        legacy_id = data["@id"]
        rm = (
            db.query(morphology.ReconstructionMorphology)
            .filter(morphology.ReconstructionMorphology.legacy_id == legacy_id)
            .first()
        )
        if not rm:
            description = data.get("description", None)
            name = data.get("name", None)
            brain_location, brain_region_id = get_brain_location_mixin(
                data, db
            )
            license_id = get_license_mixin(data, db)
            species_id, strain_id = get_species_mixin(data, db)
            db_reconstruction_morphology = morphology.ReconstructionMorphology(
                legacy_id=data.get("@id", None),
                name=name,
                description=description,
                brain_location=brain_location,
                brain_region_id=brain_region_id,
                species_id=species_id,
                strain_id=strain_id,
                license_id=license_id,
            )
            db.add(db_reconstruction_morphology)
            db.commit()
            db.refresh(db_reconstruction_morphology)
            contribution = data.get("contribution", {})
            contribution = curate.curate_contribution(contribution)
            if contribution:
                get_or_create_contribution(
                    contribution, db_reconstruction_morphology.id, db
                )
            annotations = data.get("annotation", [])
            if type(annotations) == dict:
                annotations = [annotations]
            for annotation in annotations:
                get_or_create_morphology_annotation(
                    annotation, db_reconstruction_morphology.id, db
                )


def import_morphology_feature_annotations(data_list, db):
    possible_data = [
        data
        for data in data_list
        if "NeuronMorphologyFeatureAnnotation" in data["@type"]
    ]
    for data in tqdm(possible_data):
        try:
            legacy_id = data.get("hasTarget", {}).get("hasSource", {}).get("@id", None)
            if not legacy_id:
                print(
                    "Skipping morphology feature annotation due to missing legacy id."
                )
                continue
            rm = (
                db.query(morphology.ReconstructionMorphology)
                .filter(morphology.ReconstructionMorphology.legacy_id == legacy_id)
                .first()
            )
            if not rm:
                print("skipping morphology that is not imported")
                continue
            all_measurements = []
            for measurement in data.get("hasBody", []):
                serie = measurement.get("value", {}).get("series", [])
                if type(serie) == dict:
                    serie = [serie]
                measurement_serie = [
                    morphology.MorphologyMeasurementSerieElement(
                        name=serie_elem.get("statistic", None),
                        value=serie_elem.get("value", None),
                    )
                    for serie_elem in serie
                ]

                all_measurements.append(
                    morphology.MorphologyMeasurement(
                        measurement_of=measurement.get("isMeasurementOf", {}).get(
                            "label", None
                        ),
                        measurement_serie=measurement_serie,
                    )
                )

            db_morphology_feature_annotation = morphology.MorphologyFeatureAnnotation(
                reconstruction_morphology_id=rm.id
            )
            db_morphology_feature_annotation.measurements = all_measurements
            db.add(db_morphology_feature_annotation)
            db.commit()
            db.refresh(db_morphology_feature_annotation)
        except sqlalchemy.exc.IntegrityError:
            # todo: investigate if what is actually happening
            print("2 annotations for a morphology ignoring")
            db.rollback()
            continue
        except Exception as e:
            print(f"Error: {e}")
            import ipdb

            ipdb.set_trace()
            print(data)

def import_experimental_neuron_densities(data_list, db):
    _import_experimental_densities(data_list, db, "ExperimentalNeuronDensity", density.ExperimentalNeuronDensity, curate.default_curate)

def import_experimental_bouton_densities(data_list, db):
    _import_experimental_densities(data_list, db, "ExperimentalBoutonDensity", density.ExperimentalBoutonDensity, curate.default_curate)

def import_experimental_synapses_per_connection(data_list, db):
    _import_experimental_densities(data_list, db, "ExperimentalSynapsesPerConnection", density.ExperimentalSynapsesPerConnection, curate.curate_synapses_per_connections)

def _import_experimental_densities(data_list, db, schema_type, model_type, curate_function):

    possible_data = [
        data
        for data in data_list
        if schema_type in data["@type"]
    ]

    for data in tqdm(possible_data):
        data = curate_function(data)
        legacy_id = data["@id"]
        db_element = (
            db.query(model_type)
            .filter(model_type.legacy_id == legacy_id)
            .first()
        )
        if not db_element:
            license_id = get_license_mixin(data, db)
            species_id, strain_id = get_species_mixin(data, db)
            brain_location,brain_region_id = get_brain_location_mixin(data,db)
            db_element = model_type(
                legacy_id=legacy_id,
                name=data.get("name", None),
                description=data.get("description", None),
                species_id=species_id,
                strain_id=strain_id,
                license_id=license_id,
                brain_location=brain_location,
                brain_region_id=brain_region_id,
            )
            db.add(db_element)
            db.commit()
            contribution = data.get("contribution", {})
            if contribution:
                contribution = curate.curate_contribution(contribution)
                get_or_create_contribution(
                    contribution, db_element.id, db
                )


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
    print("importing agents")
    for file_path in all_files:
        with open(file_path, "r") as f:
            data = json.load(f)
            import_agents(data, db)

    # print("importing morphologies")
    # for file_path in all_files:
    #     with open(file_path, "r") as f:
    #         data = json.load(f)
    #         import_morphologies(data, db)
    
    # print("importing morphology feature annotations")
    # for file_path in all_files:
    #     with open(file_path, "r") as f:
    #         data = json.load(f)
    #         import_morphology_feature_annotations(data, db)
    
    print("importing experimental neuron densities")
    for file_path in all_files:
        with open(file_path, "r") as f:
            data = json.load(f)
            import_experimental_neuron_densities(data, db)
    
    print("importing experimental bouton densities")
    for file_path in all_files:
        with open(file_path, "r") as f:
            data = json.load(f)
            import_experimental_bouton_densities(data, db)

    print("importing synapses per connection")
    for file_path in all_files:
        with open(file_path, "r") as f:
            data = json.load(f)
            import_experimental_synapses_per_connection(data, db)


    # "https://bbp.epfl.ch/ontologies/core/bmo/ExperimentalTrace",
    # "https://bbp.epfl.ch/ontologies/core/bmo/SingleCellExperimentalTrace",
    # "https://neuroshapes.org/Trace"

if __name__ == "__main__":
    main()
