def curate_role(role):
    if not role:
        return {"@id": "unspecified", "label": "unspecified"}
    if role["@id"] in [
        "neuronmorphology:ReconstructionRole",
        "neuron:MorphologyReconstructionRole",
        "https://bbp.epfl.ch/data/bbp/mmb-point-neuron-framework-model/NeuronMorphologyReconstruction",
        "https://bbp.epfl.ch/data/public/sscx/NeuronMorphologyReconstruction",
    ]:
        return {
            "@id": "Neuron:MorphologyReconstructionRole",
            "label": "neuron morphology reconstruction role",
        }
    if role["@id"] in [
        "neuron:ElectrophysiologyRecordingRole",
    ]:
        return {
            "@id": "Neuron:ElectrophysiologyRecordingRole",
            "label": "neuron electrophysiology recording role",
        }
    return role


def curate_annotation_body(annotation_body):
    if "Mtype" in annotation_body["@type"]:
        annotation_body["@type"] = ["MType", "AnnotationBody"]
    return annotation_body


def curate_person(person):
    if person.get("name", "") == "Weina Ji":
        person["givenName"] = "Weina"
        person["familyName"] = "Ji"
    return person


def curate_contribution(contribution):
    if type(contribution) == list:
        return [curate_contribution(c) for c in contribution]
    if (
        contribution["agent"]["@id"]
        == "f:0fdadef7-b2b9-492b-af46-c65492d459c2:ajaquier"
    ):
        contribution["agent"][
            "@id"
        ] = "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/ajaquier"
    if contribution["agent"]["@id"] == "f:0fdadef7-b2b9-492b-af46-c65492d459c2:mandge":
        contribution["agent"][
            "@id"
        ] = "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/mandge"
    return contribution

def default_curate(obj):
    return obj

def curate_synapses_per_connections(data):
    if not data.get('description', None):
        data['description'] = "unspecified" 
    return data

def curate_trace(data):
    if not data.get('description', None):
        data['description'] = "unspecified" 
    return data

def curate_brain_region(data):
    if data['@id'] == 'mba:977' and data['label'] == 'root':
        data['@id'] = 'mba:997'
    return data

def curate_etype(data):
    if data['label'] == 'TH_cAD_noscltb':
        data['definition'] = 'Thalamus continuous adapting non-oscillatory low-threshold bursting electrical type'
    if data['label'] == 'TH_cNAD_noscltb':
        data['definition'] = 'Thalamus continuous non-adapting non-oscillatory low-threshold bursting electrical type'
    if data['label'] == 'TH_dAD_ltb':
        data['definition'] = 'Thalamus delayed adapting low-threshold bursting electrical type'
        data['alt_label'] = 'Thalamus delayed adapting low-threshold bursting electrical type'
    if data['label'] == 'TH_dNAD_ltb':
        data['definition'] = 'Thalamus delayed non-adapting low-threshold bursting electrical type'
        data['alt_label'] = 'Thalamus delayed non-adapting low-threshold bursting electrical type'
    return data