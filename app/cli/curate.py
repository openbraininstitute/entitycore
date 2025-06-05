import datetime

from app.cli.brain_region_data import BRAIN_REGION_REPLACEMENTS
from app.logger import L


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
    if annotation_body.get("@id", "") == "nsg:InhibitoryNeuron":
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
    data["@id"] = str(data["@id"])
    if data["@id"] == "mba:977" and data["label"] == "root":
        data["@id"] = "mba:997"

    data["@id"] = data["@id"].replace("mba:", "")
    data["@id"] = data["@id"].replace("http://api.brain-map.org/api/v2/data/Structure/", "")

    if data["@id"] == "root":
        data["@id"] = "997"

    if data["label"] in BRAIN_REGION_REPLACEMENTS:
        data["@id"] = BRAIN_REGION_REPLACEMENTS[data["label"]]

    return data


def curate_mtype(data):
    if data["label"] == "Inhibitory":
        data["label"] = "Inhibitory neuron"
    elif data["label"] == "Excitatory":
        data["label"] = "Excitatory neuron"
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


def curate_morphology(data):
    if data.get("name", "") == "cylindrical_morphology_20.5398":
        data["subject"] = {
            "species": {
                "@id": "NCBITaxon:10090",
                "label": "Mus musculus",
            },
        }
    return data


def default_species():
    return [
        {
            "@id": "NCBITaxon:9606",
            "label": "Homo sapiens",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "NCBITaxon:8355",
            "label": "Xenopus laevis",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "NCBITaxon:10029",
            "label": "Cricetulus griseus",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "NCBITaxon:9685",
            "label": "Felis Catus",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "NCBITaxon:6619",
            "label": "Loligo pealeil",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "NCBITaxon:8407",
            "label": "Rana catesbeiana",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "NA",
            "label": "Hybrid human-mouse",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
    ]


def default_agents():
    return [
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/ikilic",
            "_self": "",
            "@type": "Person",
            "givenName": "Ilkan",
            "familyName": "Kiliç",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "f:0fdadef7-b2b9-492b-af46-c65492d459c2:ikilic",
            "_self": "",
            "@type": "Person",
            "givenName": "Ilkan",
            "familyName": "Kiliç",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        # TODO: find out who that is.
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/harikris",
            "_self": "",
            "@type": "Person",
            "givenName": "h",
            "familyName": "arikris",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/ricardi",
            "_self": "",
            "@type": "Person",
            "givenName": "Niccolò",
            "familyName": "Ricardi",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/akkaufma",
            "_self": "",
            "@type": "Person",
            "givenName": "Anna-Kristin",
            "familyName": "Kaufmann",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/gbarrios",
            "_self": "",
            "@type": "Person",
            "givenName": "Gil",
            "familyName": "Barrios",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/okeeva",
            "_self": "",
            "@type": "Person",
            "givenName": "Ayima",
            "familyName": "Okeeva",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://www.grid.ac/institutes/grid.83440.3b ",
            "_self": "",
            "@type": "Organization",
            "name": "University College London",
            "alternativeName": "UCL",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/lurie",
            "_self": "",
            "@type": "Person",
            "givenName": "Jonathan",
            "familyName": "Lurie",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        # TODO: Who dis?
        {
            "@id": "https://bbp.epfl.ch/neurosciencegraph/data/b1e71aec-0e4e-4ce3-aca2-99f1614da975",
            "_self": "",
            "@type": "Person",
            "givenName": "Uknown",
            "familyName": "Unknown",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/antonel",
            "_self": "",
            "@type": "Person",
            "givenName": "Stefano",
            "familyName": "Antonel",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/getta",
            "_self": "",
            "@type": "Person",
            "givenName": "Pavlo",
            "familyName": "Getta",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/kurban",
            "_self": "",
            "@type": "Person",
            "givenName": "Kerem",
            "familyName": "Kurban",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/courcol",
            "_self": "",
            "@type": "Person",
            "givenName": "Jean-Denis",
            "familyName": "Courcol",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/ivaska",
            "_self": "",
            "@type": "Person",
            "givenName": "Genrich",
            "familyName": "Ivaska",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/soplata",
            "_self": "",
            "@type": "Person",
            "givenName": "Austin",
            "familyName": "Soplata",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/muddapu",
            "_self": "",
            "@type": "Person",
            "givenName": "Vignayanandam",
            "familyName": "Muddapu",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "f:0fdadef7-b2b9-492b-af46-c65492d459c2:damart",
            "_self": "",
            "@type": "Person",
            "givenName": "Tanguy",
            "familyName": "Damart",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/sy",
            "_self": "",
            "@type": "Person",
            "givenName": "Mohameth François",
            "familyName": "Sy",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/mouffok",
            "_self": "",
            "@type": "Person",
            "givenName": "Sarah",
            "familyName": "Mouffok",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/lcristel",
            "_self": "",
            "@type": "Person",
            "givenName": "Leonardo",
            "familyName": "Cristel",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/serviceaccounts/users/service-account-nexus-sa",
            "_self": "",
            "@type": "Person",
            "givenName": "service-account-nexus-sa",
            "familyName": "service-account-nexus-sa",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/serviceaccounts/users/service-account-brain-modeling-ontology-ci-cd",
            "_self": "",
            "@type": "Person",
            "givenName": "service-account-brain-modeling-ontology-ci-cd",
            "familyName": "service-account-brain-modeling-ontology-ci-cd",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/service-account-bbp-dke-bluebrainatlas-sa",
            "_self": "",
            "@type": "Person",
            "givenName": "service-account-bbp-dke-bluebrainatlas-sa",
            "familyName": "service-account-bbp-dke-bluebrainatlas-sa",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/cgonzale",
            "_self": "",
            "@type": "Person",
            "givenName": "Christina",
            "familyName": "Gonzalez",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/alibou",
            "_self": "",
            "@type": "Person",
            "givenName": "Nabil",
            "familyName": "Alibou",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/service-account-bbp-dke-data-pipelines-sa",
            "_self": "",
            "@type": "Person",
            "givenName": "service-account-bbp-dke-data-pipelines-sa",
            "familyName": "service-account-bbp-dke-data-pipelines-sa",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/plurie",
            "_self": "",
            "@type": "Person",
            "givenName": "Patricia",
            "familyName": "Lurie",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/damart",
            "_self": "",
            "@type": "Person",
            "givenName": "Tanguy",
            "familyName": "Damart",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
    ]


def default_licenses():
    return [
        {
            "@id": "https://bbp.epfl.ch/neurosciencegraph/data/licenses/97521f71-605d-4f42-8f1b-c37e742a30bf",
            "_self": "https://openbluebrain.com/api/nexus/v1/resources/public/sscx/_/https:%2F%2Fbbp.epfl.ch%2Fneurosciencegraph%2Fdata%2Flicenses%2F97521f71-605d-4f42-8f1b-c37e742a30bf",
            "label": "undefined",
            "description": "undefined",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
    ]


def curate_distribution(distribution, project_context):
    if isinstance(distribution, list):
        return [curate_distribution(c, project_context) for c in distribution]
    assert distribution["@type"] == "DataDownload"
    assert distribution["contentSize"]["unitCode"] == "bytes"
    assert distribution["contentSize"]["value"] > 0
    assert distribution["digest"]["algorithm"] == "SHA-256"
    assert distribution["digest"]["value"] is not None
    if "atLocation" in distribution:
        assert distribution["atLocation"]["@type"] == "Location"
    else:
        msg = f"Distribution had not atLocation: {distribution}"
        L.warning(msg)
    return distribution
