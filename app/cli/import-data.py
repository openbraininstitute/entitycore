import argparse
import glob
import json
import os
import sys

import sqlalchemy
from sqlalchemy import func
from tqdm import tqdm

from app.cli import curate
from app.models import (
    agent,
    annotation,
    base,
    contribution,
    density,
    mesh,
    morphology,
    role,
    single_cell_experimental_trace,
)
from app.models.base import SessionLocal


def get_agent_from_legacy_id(legacy_id, db):
    use_func = func.instr
    if db.bind.dialect.name == "postgresql":
        use_func = func.strpos

    db_agent = (
        db.query(agent.Agent)
        .filter(use_func(agent.Agent.legacy_id, legacy_id) > 0)
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
    annotation_types = {
        "EType": annotation.ETypeAnnotationBody,
        "MType": annotation.MTypeAnnotationBody,
        "DataMaturity": annotation.DataMaturityAnnotationBody,
    }
    annotation_type_list = annotation_body["@type"]
    intersection = [
        value for value in annotation_type_list if value in annotation_types
    ]

    assert (
        len(intersection) == 1
    ), f"Unknown annotation body type {annotation_body['@type']}"
    db_annotation = annotation_types[intersection[0]]
    ab = (
        db.query(db_annotation)
        .filter(db_annotation.pref_label == annotation_body["label"])
        .first()
    )
    if not ab:
        if db_annotation is annotation.MTypeAnnotationBody:
            raise ValueError(f"Missing mtype in annotation body {annotation_body}")
        ab = db_annotation(pref_label=annotation_body["label"])
        db.add(ab)
        db.commit()
    return ab.id


def get_or_create_contribution(contribution_, entity_id, db):
    # Check if the contribution already exists in the database
    if type(contribution_) is list:
        for c in contribution_:
            get_or_create_contribution(c, entity_id, db)
        return None
    agent_legacy_id = contribution_["agent"]["@id"]
    db_agent = get_agent_from_legacy_id(agent_legacy_id, db)
    if not db_agent:
        print(f"Agent with legacy_id {agent_legacy_id} not found")
        return None
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


def import_licenses(data, db):
    data.append(
        {
            "@id": "https://bbp.epfl.ch/neurosciencegraph/data/licenses/97521f71-605d-4f42-8f1b-c37e742a30b",
            "label": "undefined",
            "description": "undefined",
        }
    )
    data.append(
        {
            "@id": "https://bbp.epfl.ch/neurosciencegraph/data/licenses/97521f71-605d-4f42-8f1b-c37e742a30bf",
            "label": "undefined",
            "description": "undefined",
        }
    )
    for license in data:
        db_license = (
            db.query(base.License).filter(base.License.name == license["@id"]).first()
        )
        if db_license:
            continue
        try:
            db_license = base.License(
                name=license["@id"],
                label=license["label"],
                description=license["description"],
                legacy_id=[license["@id"]],
            )

            db.add(db_license)
            db.commit()
        except Exception as e:
            print(e)
            print(license)
            raise e


def _import_annotation_body(data, db_type_, db):
    for class_elem in tqdm(data):
        if db_type_ == annotation.ETypeAnnotationBody:
            class_elem = curate.curate_etype(class_elem)
        db_elem = (
            db.query(db_type_)
            .filter(db_type_.pref_label == class_elem["label"])
            .first()
        )
        if db_elem:
            assert db_elem.definition == class_elem.get("definition", "")
            assert db_elem.alt_label == class_elem.get("prefLabel", "")
            continue
        db_elem = db_type_(
            pref_label=class_elem["label"],
            definition=class_elem.get("definition", ""),
            alt_label=class_elem.get("prefLabel", ""),
            legacy_id=[class_elem["@id"]],
        )
        db.add(db_elem)
        db.commit()


def import_mtype_annotation_body(data, db):
    # Check if the annotation body already exists in the database
    data.append(
        {
            "label": "Inhibitory neuron",
            "definition": "Inhibitory neuron",
            "prefLabel": "Inhibitory neuron",
            "@id": "https://bbp.epfl.ch/neurosciencegraph/data/annotation/mtype/Inhibitoryneuron",
        }
    )
    data.append(
        {
            "label": "Excitatory neuron",
            "definition": "Excitatory neuron",
            "prefLabel": "Excitatory neuron",
            "@id": "https://bbp.epfl.ch/neurosciencegraph/data/annotation/mtype/Excitatoryneuron",
        }
    )
    _import_annotation_body(data, annotation.MTypeAnnotationBody, db)


def import_etype_annotation_body(data, db):
    _import_annotation_body(data, annotation.ETypeAnnotationBody, db)


def import_agents(data_list, db):
    for data in data_list:
        if "Person" in data["@type"]:
            use_func = func.instr
            if db.bind.dialect.name == "postgresql":
                use_func = func.strpos
            legacy_id = data["@id"]
            db_agent = (
                db.query(agent.Person)
                .filter(use_func(agent.Agent.legacy_id, legacy_id) > 0)
                .first()
            )
            if not db_agent:
                try:
                    data = curate.curate_person(data)
                    givenName = data["givenName"]
                    familyName = data["familyName"]
                    db_agent = (
                        db.query(agent.Person)
                        .filter(
                            agent.Person.givenName == givenName,
                            agent.Person.familyName == familyName,
                        )
                        .first()
                    )
                    if db_agent:
                        ll = db_agent.legacy_id.copy()
                        ll.append(legacy_id)
                        db_agent.legacy_id = ll

                        db.commit()
                    else:
                        db_agent = agent.Person(
                            legacy_id=[legacy_id],
                            givenName=data["givenName"],
                            familyName=data["familyName"],
                        )
                        db.add(db_agent)
                        db.commit()
                except Exception as e:
                    print("Error importing person: ", data)
                    print(e)
        elif "Organization" in data["@type"]:
            legacy_id = data["@id"]

            use_func = func.instr
            if db.bind.dialect.name == "postgresql":
                use_func = func.strpos
            db_agent = (
                db.query(agent.Organization)
                .filter(use_func(agent.Agent.legacy_id, legacy_id) > 0)
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
                        ll = db_agent.legacy_id.copy()
                        ll.append(legacy_id)
                        db_agent.legacy_id = ll

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
    coordinates = data.get("brainLocation", {}).get("coordinatesInBrainAtlas", {})
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
    try:
        brain_region_id = get_or_create_brain_region(brain_region, db)
    except Exception as e:
        print(data)
        raise (e)
    return brain_location, brain_region_id


def get_species_mixin(data, db):
    species = data.get("subject", {}).get("species", {})
    assert species, "species is None"
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


def import_brain_region_meshes(data, db):
    possible_data = [data for data in data if "BrainParcellationMesh" in data["@type"]]
    possible_data = [
        data
        for data in possible_data
        if data.get("atlasRelease").get("tag", None) == "v1.1.0"
    ]
    for data in tqdm(possible_data):
        legacy_id = data["@id"]

        use_func = func.instr
        if db.bind.dialect.name == "postgresql":
            use_func = func.strpos
        rm = (
            db.query(mesh.Mesh)
            .filter(use_func(mesh.Mesh.legacy_id, legacy_id) > 0)
            .first()
        )
        if not rm:
            _, brain_region_id = get_brain_location_mixin(data, db)
            content_url = data.get("distribution").get("contentUrl")
            db_item = mesh.Mesh(
                legacy_id=[legacy_id],
                brain_region_id=brain_region_id,
                content_url=content_url,
            )
            db.add(db_item)
            db.commit()


def import_traces(data_list, db):
    possible_data = [
        data for data in data_list if "SingleCellExperimentalTrace" in data["@type"]
    ]

    for data in tqdm(possible_data):
        legacy_id = data["@id"]

        rm = (
            db.query(single_cell_experimental_trace.SingleCellExperimentalTrace)
            .filter(
                single_cell_experimental_trace.SingleCellExperimentalTrace.legacy_id
                == legacy_id
            )
            .first()
        )
        if not rm:
            data = curate.curate_trace(data)
            description = data.get("description", None)
            name = data.get("name", None)
            brain_location, brain_region_id = get_brain_location_mixin(data, db)
            license_id = get_license_mixin(data, db)
            species_id, strain_id = get_species_mixin(data, db)
            db_item = single_cell_experimental_trace.SingleCellExperimentalTrace(
                legacy_id=[data.get("@id", None)],
                name=name,
                description=description,
                brain_location=brain_location,
                brain_region_id=brain_region_id,
                species_id=species_id,
                strain_id=strain_id,
                license_id=license_id,
            )
            db.add(db_item)
            db.commit()
            db.refresh(db_item)
            contribution = data.get("contribution", {})
            contribution = curate.curate_contribution(contribution)
            if contribution:
                get_or_create_contribution(contribution, db_item.id, db)
            annotations = data.get("annotation", [])
            if isinstance(annotations, dict):
                annotations = [annotations]
            for annotation in annotations:
                get_or_create_morphology_annotation(annotation, db_item.id, db)


def import_morphologies(data_list, db):
    possible_data = [
        data for data in data_list if "ReconstructedNeuronMorphology" in data["@type"]
    ]

    for data in tqdm(possible_data):
        legacy_id = data["@id"]
        use_func = func.instr
        if db.bind.dialect.name == "postgresql":
            use_func = func.strpos
        rm = (
            db.query(morphology.ReconstructionMorphology)
            .filter(
                use_func(morphology.ReconstructionMorphology.legacy_id, legacy_id) > 0
            )
            .first()
        )
        if not rm:
            description = data.get("description", None)
            name = data.get("name", None)
            brain_location, brain_region_id = get_brain_location_mixin(data, db)
            license_id = get_license_mixin(data, db)
            species_id, strain_id = get_species_mixin(data, db)
            db_reconstruction_morphology = morphology.ReconstructionMorphology(
                legacy_id=[data.get("@id", None)],
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
            if isinstance(annotations, dict):
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
            use_func = func.instr
            if db.bind.dialect.name == "postgresql":
                use_func = func.strpos
            rm = (
                db.query(morphology.ReconstructionMorphology)
                .filter(
                    use_func(morphology.ReconstructionMorphology.legacy_id, legacy_id)
                    > 0
                )
                .first()
            )
            if not rm:
                print("skipping morphology that is not imported")
                continue
            all_measurements = []
            for measurement in data.get("hasBody", []):
                serie = measurement.get("value", {}).get("series", [])
                if isinstance(serie, dict):
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
            print(data)


def import_experimental_neuron_densities(data_list, db):
    _import_experimental_densities(
        data_list,
        db,
        "ExperimentalNeuronDensity",
        density.ExperimentalNeuronDensity,
        curate.default_curate,
    )


def import_experimental_bouton_densities(data_list, db):
    _import_experimental_densities(
        data_list,
        db,
        "ExperimentalBoutonDensity",
        density.ExperimentalBoutonDensity,
        curate.default_curate,
    )


def import_experimental_synapses_per_connection(data_list, db):
    _import_experimental_densities(
        data_list,
        db,
        "ExperimentalSynapsesPerConnection",
        density.ExperimentalSynapsesPerConnection,
        curate.curate_synapses_per_connections,
    )


def _import_experimental_densities(
    data_list, db, schema_type, model_type, curate_function
):
    possible_data = [data for data in data_list if schema_type in data["@type"]]

    for data in tqdm(possible_data):
        data = curate_function(data)
        legacy_id = data["@id"]
        use_func = func.instr
        if db.bind.dialect.name == "postgresql":
            use_func = func.strpos
        db_element = (
            db.query(model_type)
            .filter(use_func(model_type.legacy_id, legacy_id) > 0)
            .first()
        )
        if not db_element:
            license_id = get_license_mixin(data, db)
            species_id, strain_id = get_species_mixin(data, db)
            brain_location, brain_region_id = get_brain_location_mixin(data, db)
            db_element = model_type(
                legacy_id=[legacy_id],
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
                get_or_create_contribution(contribution, db_element.id, db)


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

    # engine = create_engine(
    #     "sqlite:///" + args.db, connect_args={"check_same_thread": False}
    # )
    # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    all_files = glob.glob(os.path.join(args.input_dir, "*", "*", "*.json"))
    print("importing agents")
    for file_path in all_files:
        with open(file_path) as f:
            data = json.load(f)
            import_agents(data, db)
    print("import licenses")
    with open(
        os.path.join(args.input_dir, "bbp", "licenses", "provEntity.json"),
    ) as f:
        data = json.load(f)
        import_licenses(data, db)
    print("import mtype annotations")
    with open(
        os.path.join(
            args.input_dir, "neurosciencegraph", "datamodels", "owlClass.json"
        ),
    ) as f:
        data = json.load(f)
        possible_data = [
            data for data in data if "nsg:MType" in data.get("subClassOf", {})
        ]
        import_mtype_annotation_body(possible_data, db)

    print("import etype annotations")
    with open(
        os.path.join(
            args.input_dir, "neurosciencegraph", "datamodels", "owlClass.json"
        ),
    ) as f:
        data = json.load(f)
        possible_data = [
            data for data in data if "nsg:EType" in data.get("subClassOf", {})
        ]
        import_etype_annotation_body(possible_data, db)
    print("importing brain region meshes")
    for file_path in all_files:
        with open(file_path) as f:
            data = json.load(f)
            import_brain_region_meshes(data, db)
    print("importing morphologies")
    for file_path in all_files:
        with open(file_path) as f:
            data = json.load(f)
            import_morphologies(data, db)

    print("importing morphology feature annotations")
    for file_path in all_files:
        with open(file_path) as f:
            data = json.load(f)
            import_morphology_feature_annotations(data, db)

    print("importing experimental neuron densities")
    for file_path in all_files:
        with open(file_path) as f:
            data = json.load(f)
            import_experimental_neuron_densities(data, db)

    print("importing experimental bouton densities")
    for file_path in all_files:
        with open(file_path) as f:
            data = json.load(f)
            import_experimental_bouton_densities(data, db)

    print("importing synapses per connection")
    for file_path in all_files:
        with open(file_path) as f:
            data = json.load(f)
            import_experimental_synapses_per_connection(data, db)

    # "https://bbp.epfl.ch/ontologies/core/bmo/ExperimentalTrace",
    # "https://bbp.epfl.ch/ontologies/core/bmo/SingleCellExperimentalTrace",
    # "https://neuroshapes.org/Trace"
    for file_path in all_files:
        with open(file_path) as f:
            data = json.load(f)
            import_traces(data, db)


if __name__ == "__main__":
    main()
