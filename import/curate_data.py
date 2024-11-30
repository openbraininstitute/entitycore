def curate_role(role):
    if not role:
        return {"@id": "unspecified", "label": "unspecified"}
    if role["@id"] in [
        "neuronmorphology:ReconstructionRole",
        "neuron:MorphologyReconstructionRole",
        "https://bbp.epfl.ch/data/bbp/mmb-point-neuron-framework-model/NeuronMorphologyReconstruction",
        'https://bbp.epfl.ch/data/public/sscx/NeuronMorphologyReconstruction',
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
