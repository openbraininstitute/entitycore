import datetime


def curate_role(role):
    if not role:
        return {"@id": "unspecified", "label": "unspecified"}

    if role["@id"] in {
        "neuronmorphology:ReconstructionRole",
        "neuron:MorphologyReconstructionRole",
        "https://bbp.epfl.ch/data/bbp/mmb-point-neuron-framework-model/NeuronMorphologyReconstruction",
        "https://bbp.epfl.ch/data/public/sscx/NeuronMorphologyReconstruction",
    }:
        role = {
            "@id": "Neuron:MorphologyReconstructionRole",
            "label": "neuron morphology reconstruction role",
        }
    elif role["@id"] == "neuron:ElectrophysiologyRecordingRole":
        role = {
            "@id": "Neuron:ElectrophysiologyRecordingRole",
            "label": "neuron electrophysiology recording role",
        }

    return role


def curate_annotation_body(annotation_body):
    if "Mtype" in annotation_body["@type"]:
        annotation_body["@type"] = ["MType", "AnnotationBody"]

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
    elif contribution["agent"]["@id"] == "f:0fdadef7-b2b9-492b-af46-c65492d459c2:mandge":
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

    return data


def curate_etype(data):
    if data["label"] == "TH_cAD_noscltb":
        data["definition"] = (
            "Thalamus continuous adapting non-oscillatory low-threshold bursting electrical type"
        )
    elif data["label"] == "TH_cNAD_noscltb":
        data["definition"] = (
            "Thalamus continuous non-adapting non-oscillatory low-threshold bursting electrical type"  # noqa: E501
        )
    elif data["label"] == "TH_dAD_ltb":
        data["definition"] = "Thalamus delayed adapting low-threshold bursting electrical type"
        data["alt_label"] = "Thalamus delayed adapting low-threshold bursting electrical type"
    elif data["label"] == "TH_dNAD_ltb":
        data["definition"] = "Thalamus delayed non-adapting low-threshold bursting electrical type"
        data["alt_label"] = "Thalamus delayed non-adapting low-threshold bursting electrical type"

    return data


def default_agents():
    return [
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/ikilic",
            "@type": "Person",
            "givenName": "Ilkan",
            "familyName": "Kilic",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        # TODO: find out who that is.
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/harikris",
            "@type": "Person",
            "givenName": "h",
            "familyName": "arikris",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/ricardi",
            "@type": "Person",
            "givenName": "Nicolo",
            "familyName": "Ricardi",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/akkaufma",
            "@type": "Person",
            "givenName": "Anna-Kristin",
            "familyName": "Kaufmann",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/gbarrios",
            "@type": "Person",
            "givenName": "Gil",
            "familyName": "Barrios",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/okeeva",
            "@type": "Person",
            "givenName": "Ayima",
            "familyName": "Okeeva",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
    ]


def default_licenses():
    return [
        {
            "@id": "https://bbp.epfl.ch/neurosciencegraph/data/licenses/97521f71-605d-4f42-8f1b-c37e742a30b",
            "label": "undefined",
            "description": "undefined",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/neurosciencegraph/data/licenses/97521f71-605d-4f42-8f1b-c37e742a30bf",
            "label": "undefined",
            "description": "undefined",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
    ]
