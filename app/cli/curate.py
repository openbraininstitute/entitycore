def curate_role(role):
    if not role:
        return {"@id": "unspecified", "label": "unspecified"}
    if role["@id"] in {
        "neuronmorphology:ReconstructionRole",
        "neuron:MorphologyReconstructionRole",
        "https://bbp.epfl.ch/data/bbp/mmb-point-neuron-framework-model/NeuronMorphologyReconstruction",
        "https://bbp.epfl.ch/data/public/sscx/NeuronMorphologyReconstruction",
    }:
        return {
            "@id": "Neuron:MorphologyReconstructionRole",
            "label": "neuron morphology reconstruction role",
        }
    if role["@id"] == "neuron:ElectrophysiologyRecordingRole":
        return {
            "@id": "Neuron:ElectrophysiologyRecordingRole",
            "label": "neuron electrophysiology recording role",
        }
    return role


def curate_annotation_body(annotation_body):
    if "Mtype" in annotation_body["@type"]:
        annotation_body["@type"] = ["MType", "AnnotationBody"]
    if annotation_body["@id"] == "nsg:InhibitoryNeuron":
        annotation_body["label"] = "Inhibitory neuron"
    return annotation_body


def curate_person(person):
    if name := person.get("name", ""):
        if name == "Weina Ji":
            person["givenName"] = "Weina"
            person["familyName"] = "Ji"
        elif name == "None None":  # noqa: SIM114
            person["givenName"] = "bbp-dke-bluebrainatlas-sa"
            person["familyName"] = "bbp-dke-bluebrainatlas-sa"
        elif name == "None brain-modeling-ontology-ci-cd":
            person["givenName"] = "bbp-dke-bluebrainatlas-sa"
            person["familyName"] = "bbp-dke-bluebrainatlas-sa"

    return person


def curate_contribution(contribution):
    if isinstance(contribution, list):
        return [curate_contribution(c) for c in contribution]
    if contribution["agent"]["@id"] == "f:0fdadef7-b2b9-492b-af46-c65492d459c2:ajaquier":
        contribution["agent"]["@id"] = "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/ajaquier"
    if contribution["agent"]["@id"] == "f:0fdadef7-b2b9-492b-af46-c65492d459c2:mandge":
        contribution["agent"]["@id"] = "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/mandge"
    return contribution


def default_curate(obj):
    return obj


def curate_synapses_per_connections(data):
    if not data.get("description", None):
        data["description"] = "unspecified"
    return data


def curate_trace(data):
    if not data.get("description", None):
        data["description"] = "unspecified"
    return data


def curate_brain_region(data):
    if data["@id"] == "mba:977" and data["label"] == "root":
        data["@id"] = "mba:997"
    data["@id"] = data["@id"].replace("mba:", "http://api.brain-map.org/api/v2/data/Structure/")
    if data["@id"] == "http://api.brain-map.org/api/v2/data/Structure/root":
        data["@id"] = "http://api.brain-map.org/api/v2/data/Structure/997"
    return data


def curate_etype(data):
    if data["label"] == "TH_cAD_noscltb":
        data["definition"] = (
            "Thalamus continuous adapting non-oscillatory low-threshold bursting electrical type"
        )
    if data["label"] == "TH_cNAD_noscltb":
        data["definition"] = (
            "Thalamus continuous non-adapting non-oscillatory low-threshold bursting electrical type"  # noqa: E501
        )
    if data["label"] == "TH_dAD_ltb":
        data["definition"] = "Thalamus delayed adapting low-threshold bursting electrical type"
        data["alt_label"] = "Thalamus delayed adapting low-threshold bursting electrical type"

    if data["label"] == "TH_dNAD_ltb":
        data["definition"] = "Thalamus delayed non-adapting low-threshold bursting electrical type"
        data["alt_label"] = "Thalamus delayed non-adapting low-threshold bursting electrical type"
    return data


def curate_morphology(data):
    if data.get("name", "") == "cylindrical_morphology_20.5398":
        data["subject"] = {
            "species": {
                "@id": "NCBITaxon:10090",
                "label": "Mus musculus",
            },
        }
    return data
