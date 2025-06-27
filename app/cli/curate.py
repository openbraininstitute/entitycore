import datetime
import re

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


def curate_mtype(annotation_body):
    if annotation_body.get("@id", "") == "nsg:InhibitoryNeuron":
        annotation_body["label"] = "Inhibitory neuron"
    if (
        annotation_body.get("@id", "")
        == "https://scicrunch.org/scicrunch/interlex/view/ilx_0109553?searchTerm=pyramidal%20neuron"
    ):
        annotation_body["@id"] = "nsg:PyramidalNeuron"
        annotation_body["label"] = "Pyramidal Neuron"
    if annotation_body.get("label", "") == "L4CHC":
        annotation_body["label"] = "L4_ChC"
    if annotation_body.get("label", "") == "L2_SBC":
        annotation_body["label"] = "L23_SBC"
    if annotation_body.get("label", "") in {
        "L6UPC",
        "L6NGC",
        "L4TPC",
        "L23BTC",
        "L4DBC",
        "L2SBC",
        "L5DBC",
        "L4BTC",
        "L6IPC",
        "L6BTC",
        "L5BP",
        "L23SBC",
        "L4BP",
        "L6HPC",
        "L2IPC",
        "L23NGC",
        "L23BP",
        "L5TPC",
        "L2TPC",
        "L6BPC",
        "L3TPC",
        "L4UPC",
        "L23MC",
        "L5NBC",
    }:
        label = annotation_body["label"]
        # Insert "_" after the last number in label
        annotation_body["label"] = re.sub(r"(\d+)(?!.*\d)", r"\1_", label)
    return annotation_body


def curate_annotation_body(annotation_body):
    if "Mtype" in annotation_body["@type"]:
        annotation_body["@type"] = ["MType", "AnnotationBody"]
    if "MType" in annotation_body["@type"]:
        return curate_mtype(annotation_body)
    return annotation_body


def curate_person(person):
    ignore = False
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
        elif name in {"Jane Doe", "Daniel Fernandez Test"}:
            ignore = True

    return person, ignore


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
    if (
        data.get("synapticPathway")
        and data.get("synapticPathway").get("preSynaptic")
        and len(data.get("synapticPathway")["preSynaptic"]) > 1
        and data.get("synapticPathway")["preSynaptic"][1].get("label") == "Schaffer axon collateral"
    ):
        data["synapticPathway"]["preSynaptic"][1]["label"] = "Schaffer collateral associated cell"
    return data


def curate_trace(data):
    if not data.get("description", None):
        data["description"] = "unspecified"

    return data


def curate_brain_region(data):
    data["@id"] = str(data["@id"])
    if data["@id"] == "mba:977" and data["label"] == "root":
        data["@id"] = "mba:997"
    if (
        data["@id"]
        == "http://bbp.epfl.ch/neurosciencegraph/ontologies/core/brainregion/Isocortex_L1"
    ):
        data["@id"] = "http://api.brain-map.org/api/v2/data/Structure/315"
    if data["@id"] == "http://bbp.epfl.ch/neurosciencegraph/ontologies/core/brainregion/CA_SP":
        data["@id"] = "http://api.brain-map.org/api/v2/data/Structure/375"

    data["@id"] = data["@id"].replace("mba:", "")
    data["@id"] = data["@id"].replace("http://api.brain-map.org/api/v2/data/Structure/", "")

    if data["@id"] == "root":
        data["@id"] = "997"

    if data["label"] in BRAIN_REGION_REPLACEMENTS:
        data["@id"] = BRAIN_REGION_REPLACEMENTS[data["label"]]

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


HUMAN_DATA_FIX = {
    "5900396223": "Interneuron",
    "37128855703": "Interneuron",
    "3050310721": "Pyramidal neuron",
    "38529456032": "Interneuron",
    "6932905828": "Pyramidal neuron",
    "4548314867": "Pyramidal neuron",
    "33403731797": "Pyramidal neuron",
    "5032293103": "Pyramidal neuron",
    "3866198827": "Pyramidal neuron",
    "28584232962": "Pyramidal neuron",
    "29585585515": "Pyramidal neuron",
    "3223274014": "Pyramidal neuron",
    "5803153406": "Pyramidal neuron",
    "38557957454": "Pyramidal neuron",
    "39184792410": "Pyramidal neuron",
    "4245985431": "Interneuron",
    "7083515830": "Pyramidal neuron",
    "42685892214": "Pyramidal neuron",
    "5776462380": "Pyramidal neuron",
    "30008794370": "Pyramidal neuron",
    "30589097324": "Interneuron",
    "41790705830": "Pyramidal neuron",
    "32485080076": "Pyramidal neuron",
    "27696039474": "Pyramidal neuron",
    "3199182914": "Pyramidal neuron",
    "4742901619": "Pyramidal neuron",
    "37781243320": "Inhibitory neuron",
    "6791523753": "Inhibitory neuron",
    "2364880736": "Pyramidal neuron",
    "30941549387": "Inhibitory neuron",
    "5541328846": "Inhibitory neuron",
    "42542320769": "Pyramidal neuron",
    "2062684707": "Pyramidal neuron",
    "1 Human Temp A20 ID AB1 porta11 sec1 capa3 cel 6-soma z corr 1,7-annotated_OK "
    "cell body": "L3_PC",
    "11 Human Temp A20 ID AB1 porta11 sec1 capa3 cel 8-soma z corr "
    "1,7-annotated_OK no err": "L3_PC",
    "12 Human Temp A20 ID AB1 porta11 sec1 capa3 cel 10-soma z corr 1,7-annotated_OK "
    "no err": "L3_PC",
    "13 Human temp a20 idab1 porta19 sec1 cel11-soma z corr 1,7-annotated_OK cell "
    "body_thick ending_disjoint branch": "L3_PC",
    "14\xa0 human temp a20 idab2 bl 14 bd3 n18 cel14-soma-corr1,7z-annotated_OK "
    "disjoint branch": "L3_PC",
    "15 Human temp idif10 porta1 sec1 cel15-soma z corr 1-annotated_OK cell body": "L3_PC",
    "16 Human temp idif10 porta2 sec1 cel4-soma z corr 1-annotated_OK no err": "L3_PC",
    "17 Human temp idif10 porta2 sec1 cel18-soma z corr 1-annotated_OK cell body": "L3_PC",
    "18 human temp idif12 porta2 sec1 cel8-soma-corr1,7z-annotated_OK cell body": "L3_PC",
    "19 Human temp idm16 porta1 sec1 cel2-somaz corr 1,7-annotated_OK cel body_false "
    "nodes_corr api ini": "L3_PC",
    "20 Human temp a20 idab1 porta19 sec1 cel26-soma z corr 1,7-annotated_OK thick "
    "ending_trifur false branch": "L3_PC",
    "21 human temp a20 idab1 porta11 sec1 cel7 soma-corr1,7z-annotated_OK false node": "L3_PC",
    "22 human temp a20 idab1 porta19 sec1 cel10 soma-corr1,7z-annotated_OK "
    "cell body_false nodes": "L3_PC",
    "23 human temp a20 idab1 porta19 sec1 cel12 soma-corr1,7z-annotated_OK no err": "L3_PC",
    "24 human temp a20 idab1 porta19 sec1 cel17 soma-corr1,7z-annotated_OK false nodes": "L3_PC",
    "25 human temp a20 idab1 porta19 sec1 cel18 soma-corr1,7z-annotated_OK no err": "L3_PC",
    "26 human temp a20 idab1 porta19 sec1 cel20 soma-corr1,7z-annotated_OK "
    "cell body_thick ending_false node": "L3_PC",
    "27 human temp a20 idab1 porta19 sec1 cel21 soma-corr1,7z-annotated_OK no err": "L3_PC",
    "28 human temp a20 idab1 porta19 sec1 cel22 soma-corr1,7z-annotated_OK corr ax ini": "L3_PC",
    "29 human temp a20 idab1 porta19 sec1 cel24 soma-corr1,7z-annotated_OK false node": "L3_PC",
    "3 Human temp a20 idab2 bl14 bd3 n18 cel17-soma z corr 1,7-annotated_OK "
    "false nodes_false trifur": "L3_PC",
    "30 human temp a20 idab1 porta19 sec1 cel26 soma-corr1,7z-annotated_OK "
    "thick ending_false node": "L3_PC",
    "31 human temp a20 idab1 porta19 sec1 cel27 soma-corr1,7z-annotated_OK cell body": "L3_PC",
    "32 human temp a20 idab2 bl14 bd3 n15 cel2 soma-corr1,7z-annotated_OK "
    "cell body_false node": "L3_PC",
    "33 human temp a20 idab2 bl14 bd3 n15 cel8 soma-corr1,7z-annotated_OK thick endings": "L3_PC",
    "34 human temp a20 idab2 bl14 bd3 n18 cel12 soma-corr1,7z-annotated_OK no err": "L3_PC",
    "35 human temp a20 idab2 bl14 bd3 n18 cel13 soma-corr1,7z-annotated_OK cell body_thick "
    "ending_false node_2 false branch": "L3_PC",
    "36 human temp a20 idab2 bl14 bd3 n18 cel15 soma-corr1,7z-annotated_OK "
    "cell body_false node": "L3_PC",
    "37 human temp a20 idab2 bl14 bd3 n18 cel16 soma-corr1,7z-annotated_OK cell body_err "
    "ini basal_ false node": "L3_PC",
    "38 human temp a20 idab2 bl14 bd3 n18 cel21 soma-corr1,7z-annotated_OK cell body": "L3_PC",
    "39 human temp a20 idab2 bl14 bd3 n18 sec1 cel4 soma-corr1,7z-annotated_OK no err": "L3_PC",
    "40 human temp a20 idab2 bl14 bd3 n18 sec1 cel11 soma-corr1,7z-annotated_OK no err": "L3_PC",
    "41 human temp a20 idab2 bl14 bd3 n18 sec1 cel18 soma-corr1,7z-annotated_OK "
    "thick ending": "L3_PC",
    "42 human temp a20 idab2 bl14 bd3 n18 sec1 cel19 soma-corr1,7z-annotated_OK "
    "cell body_false node": "L3_PC",
    "43 human temp a20 idab2 bl14 bd3 n18 sec1 cel20 soma-corr1,7z-annotated_OK no err": "L3_PC",
    "44 human temp idif6 porta1 sec1 cel3 soma-corr1,7z-annotated_OK cell body_false node": "L3_PC",
    "45 human temp idif6 porta1 sec1 cel4 soma-corr1,7z-annotated_OK thick ending": "L3_PC",
    "46 human temp idif6 porta1 sec1 cel5 soma-corr1,7z-annotated_OK false nodes": "L3_PC",
    "47 human temp idif6 porta1 sec1 cel7 soma-corr1,7z-annotated_OK no err_corr ini ax": "L3_PC",
    "48 human temp idif6 porta1 sec1 cel14 soma-corr1,7z-annotated_OK cell body_thick "
    "ending_false node": "L3_PC",
    "49 human temp idif6 porta1 sec1 cel15 soma-corr1,7z-annotated_OK corr basal ini": "L3_PC",
    "50 human temp idif6 porta2 sec1 cel4 soma-corr1,7z-annotated 2 nodes, 1 trifur, "
    "fat end-annotated OK": "L3_PC",
    "51 human temp idif6 porta2 sec1 cel6 soma-corr1,7z-annotated 3 nodes, "
    "2 narr st, end L": "L3_PC",
    "52 human temp idif6 porta2 sec1 cel7 soma-corr1,7z-annotated ok": "L3_PC",
    "53 human temp idif6 porta2 sec1 cel8 soma-corr1,7z-annotated fat end": "L3_PC",
    "54 human temp idif6 porta2 sec1 cel10 soma-corr1,7z-annotated 1 node, err points": "L3_PC",
    "55 human temp idif6 porta2 sec1 cel11 soma-corr1,7z-annotated ok": "L3_PC",
    "57 human temp idif6 porta2 sec1 cel17 soma-corr1,7z-annotated fat end": "L3_PC",
    "58 human temp idif10 porta1 sec1 cel5 soma-corr1z-annotated narr st": "L3_PC",
    "59 human temp a20 idab1 porta19 sec1 cel25 soma-corr1,7z-annotated narr st": "L3_PC",
    "6 Human temp idm 16 porta1 sec1 cel10-soma z corr 1,7-annotated_OK false node": "L3_PC",
    "61 human temp idif10 porta1 sec1 cel10 soma-corr1z-annotated 1node, 2 fat end, "
    "2 nar st": "L3_PC",
    "62 human temp idif10 porta1 sec1 cel12 soma-corr1z-annotated 1 node": "L3_PC",
    "63 human temp idif10 porta1 sec1 cel18 soma-corr1z-annotated narr st, end G": "L3_PC",
    "64 human temp idif10 porta1 sec1 cel24 soma-corr1z-annotated narr st, "
    "fat end, 1 trif": "L3_PC",
    "65 human temp idif10 porta1 sec1 cel26 soma-corr1z-annotated narr st, 1 node": "L3_PC",
    "66 human temp idif10 porta2 sec1 cel6 soma-corr1z-annotated narr st, 1 node": "L3_PC",
    "67 human temp idif10 porta2 sec1 cel7 soma-corr1z-annotated narr st, 1 node": "L3_PC",
    "69 human temp idif10 porta2 sec1 cel9 soma-corr1z-annotated narr st": "L3_PC",
    "70 human temp idif10 porta2 sec1 cel10 soma-corr1z-annotated ok": "L3_PC",
    "71 human temp idif10 porta2 sec1 cel11 soma-corr1z-annotated narr st, 2 node": "L3_PC",
    "72 human temp idif10 porta2 sec1 cel14 soma-corr1z-annotated narr st": "L3_PC",
    "74 human temp idif12 porta1 sec1 cel11 soma-corr1,7z-annotated 1 node": "L3_PC",
    "75 human temp idif12 porta1 sec1 cel19 soma-corr1,7z-annotated fat end": "L3_PC",
    "76 human temp idif12 porta2 sec1 cel16 soma-corr1,7z-annotated 2 narr st, fat end, "
    "2 false branch, end G": "L3_PC",
    "77 human temp idif12 porta2 sec1 cel17 soma-corr1,7z-annotated 4 narr st, corr 1 "
    "branch": "L3_PC",
    "78 human temp idif12 porta2 sec1 cel22 soma-corr1,7z-annotated 3 narr st, 1 node": "L3_PC",
    "8 human temp idif6 porta 2 capa3 cel15-soma-corr1,7z-annotated_OK cell body": "L3_PC",
    "80 human temp idm16 porta1 sec1 cel3 soma-corr1,7z-annotated 1 narr st": "L3_PC",
    "81 human temp idm16 porta1 sec1 cel8 soma-corr1,7z-annotated nar st, false node": "L3_PC",
    "82 human temp idm16 porta1 sec1 cel9 soma-corr1,7z-annotated narr st": "L3_PC",
    "83 human temp idm16 porta1 sec1 cel12 soma-corr1,7z-annotated ok": "L3_PC",
    "84 human temp idm16 porta1 sec1 cel13 soma-corr1,7z-annotated false node": "L3_PC",
    "86 human temp idm16 porta1 sec1 cel15 soma-corr1,7z-annotated ok": "L3_PC",
    "87 human temp idm16 porta3 sec1 cel 25 soma-corr1,7z-annotated narr st, 2 false nodes, 1 "
    "false branch": "L3_PC",
    "88 human temp idm16 porta3 sec1 cel7 soma-corr1,7z-annotated false node": "L3_PC",
    "89 human temp idm16 porta3 sec1 cel8 soma-corr1,7z-annotated ending G": "L3_PC",
    "90 human temp idm16 porta3 sec1 cel8bis soma-corr1,7z-annotated narr st, fat end": "L3_PC",
    "92 human temp idm16 porta3 sec1 cel10 soma-corr1,7z-annotated ok": "L3_PC",
    "93 human temp idm16 porta3 sec1 cel13 soma-corr1,7z-annotated ok": "L3_PC",
    "0409_H50_01": "L23_PC",
    "0471_H50-03": "L23_PC",
    "0520_GH_111221": "L23_PC",
    "0525_Martha_Human_1601": "L23_PC",
    "0528_Thijs_8juni_slice2": "L23_PC",
    "0547_GH_100316_I_cell2": "L23_PC",
    "0548_GH_100316_I_cell1": "L23_PC",
    "0575_Thijs_H04_01_cell1": "L23_PC",
    "0594_H53_03_": "L23_PC",
    "0616_Hans_Setup_20091110_Ctx3": "L23_PC",
    "0620_Natalia_20091110_Ctx_Cel1_Human": "L23_PC",
    "0643_H50_02": "L23_PC",
    "0660_H53_02": "L23_PC",
    "0675_H42_04": "L23_PC",
    "0749_H49_01": "L23_PC",
    "0782_H41_05_Cell3": "L23_PC",
    "0789_H41_03": "L23_PC",
    "0790_H42_03": "L23_PC",
    "0791_H01-01_cell1": "L23_PC",
    "0802_Thijs_H02_02": "L23_PC",
    "0820_H19_03_cell2": "L23_PC",
    "0849_H53_03": "L23_PC",
    "0861_Thijs_H04_01_cell2": "L23_PC",
    "0876_H41_05_Cell2": "L23_PC",
    "0893_H03-01_cell3": "L23_PC",
    "0893_H03-01_cell4": "L23_PC",
    "0918_H43_02": "L23_PC",
    "0920_H19_03_cell1": "L23_PC",
    "0925_Rhi13313cell1+2": "L23_PC",
    "0945_H35_02_J": "L23_PC",
    "0945_H42_05": "L23_PC",
    "0952_H53_01": "L23_PC",
    "0960_Thijs_H0202_cell2": "L23_PC",
    "0965_H42-09(p)": "L23_PC",
    "0974_H01-01_cell2": "L23_PC",
    "0975_Thijs_H39_03": "L23_PC",
    "0978_090513_GH_3_cell5": "L23_PC",
    "0986_GH100622_I_Cell4": "L23_PC",
    "0988_H41_05_Cell1": "L23_PC",
    "0991_H42-06": "L23_PC",
    "1008_GH100622_I_Cell3": "L23_PC",
    "1008_H12.031.TV.01": "L23_PC",
    "1014_H38_01_160113": "L23_PC",
    "1023_H43_03": "L23_PC",
    "1029_090513_GH_3_cell1": "L23_PC",
    "1049_GH100622_I_Cell2": "L23_PC",
    "1052_Thijs_H01_04": "L23_PC",
    "1056_H03-01_cell5": "L23_PC",
    "1058_Thijs_22juni_slice3": "L23_PC",
    "1063_H31_02": "L23_PC",
    "1064_Thijs_2010-09-29_slice1_cell2": "L23_PC",
    "1065_H23.29.235.11.01.07": "L4_PC",
    "1067_H38_01_160113_cell2": "L23_PC",
    "1067_Thijs_H40_02_cel1": "L23_PC",
    "1071_090513_GH_3_cell2": "L23_PC",
    "1072_H42-10": "L23_PC",
    "1081_H42-10": "L23_PC",
    "1084_GH100622_I_Cell1": "L23_PC",
    "1085_H22.29.210.11.01.03": "L23_PC",
    "1094_H03-01_cell6": "L23_PC",
    "1109_H21.29.194.11.01.11": "L23_PC",
    "1113_Thijs_H39_01": "L23_PC",
    "1120_AK_2017_03_08_H6": "L23_PC",
    "1125_H41_06_Thijs2013-02-20": "L23_PC",
    "1129_H22.29.210.11.01.01": "L23_PC",
    "1148_H42_01_": "L23_PC",
    "1164_Natalia_210910_slice1_cell2-3-4": "L23_PC",
    "1165_Thijs_2010-09-29_slice1_cell1": "L23_PC",
    "1168_090513_GH_2": "L23_PC",
    "1174_H53_01_": "L23_PC",
    "1182_H40_04": "L23_PC",
    "1192_H03-01_cell7": "L23_PC",
    "1193_H23.29.235.11.02.02": "L4_PC",
    "1195_H21.29.192.11.01.13": "L4_PC",
    "1198_H22.29.218.11.02.07": "L4_PC",
    "1202_H41_01": "L23_PC",
    "1204_H42_02": "L23_PC",
    "1209_H22.29.209.11.92.01": "L23_PC",
    "1230_H20.29.187.11.01.03": "L23_PC",
    "1252_H22.29.218.11.02.06": "L5_PC",
    "1277_H42_01_": "L23_PC",
    "1307_H22-02_cell1": "L4_PC",
    "1308_AK.19.04.17.H3.Cell2": "L4_PC",
    "1329_RBP201010_cell3-6_3": "L4_PC",
    "1336_H13048TV07": "L4_PC",
    "1350_H20.29.174.11.51.01": "L5_PC",
    "1352_AK.19.04.17.H1_Cell3": "L23_PC",
    "1352_Diana_human_130410_slice1_cel1": "L4_PC",
    "1352_H01-01_cell3": "L4_PC",
    "1364_H19.29.140.11.51": "L5_PC",
    "1364_H20.29.174.11.51.02": "L5_PC",
    "1366_Thijs_H30_01_cel2": "L4_PC",
    "1396_Thijs_H40_01": "L4_PC",
    "1398_H20.29.173.11.51_1": "L5_PC",
    "1426_AK_2017_04_19_S1_H1_N3": "L23_PC",
    "1443_AK.19.04.17.H1_Cell2": "L23_PC",
    "1487_H21.29.201.11.02.04": "L5_PC",
    "1490_H22.29.223.11.01.02": "L23_PC",
    "1496_Thijs_22juni_slice1_cell3": "L4_PC",
    "1502_H43-04": "L4_PC",
    "1504_H12035TV06_nr2": "L23_PC",
    "1514_H21.29.205.11.91.01": "L5_PC",
    "1521_AK.19.04.17.H3.Cell1": "L4_PC",
    "1526_RBP_201010_cell3-6_cell2": "L4_PC",
    "1532_H20.29.173.11.51_2": "L5_PC",
    "1533_H21.29.201.11.02.05": "L5_PC",
    "1538_H12035TV06_nr1": "L4_PC",
    "1549_H12035TV01": "L23_PC",
    "1564_Thijs_H04_01_cel3": "L4_PC",
    "1581_Thijs_H40_03": "L4_PC",
    "1584_Thijs_H30_02": "L4_PC",
    "1588_H21.29.205.11.91.02": "L5_PC",
    "1635_Natalia_Ctx_20091111_Slice1": "L4_PC",
    "1636_H12035TV08": "L4_PC",
    "1637_H21.29.206.11.91.01": "L4_PC",
    "1640_Diana_human_130410_slice2_cel1": "L4_PC",
    "1644_H20.182.11.01.01": "L5_PC",
    "1645_H21.29.194.11.01.10": "L5_PC",
    "1645_H22.29.219.11.72.01": "L5_PC",
    "1657_H20.29.180.11.01.02": "L5_PC",
    "1660_H21.29.201.11.02.02": "L5_PC",
    "1665_H20.29.190.11.01.05": "L5_PC",
    "1670_H20.29.183.11.03.01": "L4_PC",
    "1671_H21.29.194.11.01.05": "L5_PC",
    "1678_H21.29.203.11.91.05": "L5_PC",
    "1685_H12041TV04": "L4_PC",
    "1686_H20.29.180.11.01.01": "L5_PC",
    "1695_H21.29.194.11.01.01": "L5_PC",
    "1703_H12035TV02_nr1": "L4_PC",
    "1705_H22.29.219.11.72.02": "L4_PC",
    "1708_H21.29.194.11.01.06": "L5_PC",
    "1718_H21.29.194.11.01.14": "L5_PC",
    "1726_H21.29.194.11.01.09": "L5_PC",
    "1737_H21.29.205.11.02.05": "L5_PC",
    "1746_Natalia_Ctx_20091111_Slice1": "L5_PC",
    "1752_H21.29.205.11.02.06": "L5_PC",
    "1760_H12035TV02_nr2": "L4_PC",
    "1784_H22.29.209.11.93.01": "L4_PC",
    "1786_H37_02": "L5_PC",
    "1826_JAH38-01-160113": "L5_PC",
    "1827_H21_29_197_11_01": "L5_PC",
    "1827_H21.29.203.11.91.01": "L5_PC",
    "1830_H22.29.223.11.01.05": "L4_PC",
    "1833_Thijs_human_13april_slice2_cell1": "L5_PC",
    "1844_H21.29.206.11.62.02": "L5_PC",
    "1846_Thijs_Ctx_20091111_Slice1_Cel2": "L5_PC",
    "1856_H22.29.209.11.91.04": "L4_PC",
    "1858_H22.29.210.11.01.02": "L4_PC",
    "1860_H22.29.209.11.91.03": "L4_PC",
    "1866_H22.29.219.11.91.01": "L5_PC",
    "1879_Thijs_H27_02": "L5_PC",
    "1885_H20.29.190.11.03.09": "L5_PC",
    "1886_H21.29.197.11.01.04": "L5_PC",
    "1916_H21.29.194.11.01.04": "L5_PC",
    "1924_H21.29.203.11.91.06": "L5_PC",
    "1925_H20.182.11.02.03": "L5_PC",
    "1930_H13049RMO1_2": "L5_PC",
    "1935_H21.29.205.11.01.01": "L5_PC",
    "1939_Thijs_human_13april_slice2_cell2": "L5_PC",
    "1941_H22.29.209.11.91.01": "L4_PC",
    "1945_THH38-06-160113": "L5_PC",
    "1949_H20.29.206.11.93.01": "L4_PC",
    "1959_AK.23.05.18": "L5_PC",
    "1960_Thijs_Ctx_20091111_Slice1_Cel2": "L5_PC",
    "1964_H21.29.194.11.01.13": "L5_PC",
    "1989_H21.29.194.11.01.12": "L5_PC",
    "1990_H21.29.194.11.01.02": "L5_PC",
    "2022_H21.29.205.11.01.03": "L5_PC",
    "2040_H22_01_cell1": "L5_PC",
    "2045_H21.29.206.11.02.07": "L5_PC",
    "2057_H21_29_197_11_01_03": "L5_PC",
    "2088_H12.032.TV.03.01": "L5_PC",
    "2102_H20.29.190.11.01.07": "L6_PC",
    "2150_H21.29.205.11.01.02": "L5_PC",
    "2155_H20.29.183.11.03.02": "L6_PC",
    "2155_H22.29.215.11.71.09": "L5_PC",
    "2206_Thijs_H04_02_cell3": "L6_PC",
    "2219_H21.29.194.11.01.03": "L6_PC",
    "2229_H21.29.206.11.01.01": "L5_PC",
    "2236_Thijs_H04_02_cell4": "L6_PC",
    "2237_H21.29.209.11.91.02": "L5_PC",
    "2355_H21.29.206.11.01.05": "L5_PC",
    "2385_H21.29.206.11.01.04": "L5_PC",
    "2394_H20.29.173.11.51.01.01": "L5_PC",
    "2400_H22.29.223.11.01.08": "L5_PC",
    "2424_Thijs_H04_02_cell1": "L6_PC",
    "2467_Thijs_Ctx_20091111_Slice1_Cel1": "L6_PC",
    "2475_H12.034.TV.01_Cell1": "L5_PC",
    "2476_AK.21.03.18": "L5_PC",
    "2559_Thijs_H04_02_cell2": "L6_PC",
    "2576_H32_03": "L6_PC",
    "2596_H21.29.206.11.01.02.": "L5_PC",
    "2606_Thijs_H03_05_cell2": "L6_PC",
    "3124_H13049RMO1_1": "L5_PC",
    "H21.29.187.11.42.01": "L23_PC",
    "H21.29.187.11.44.01": "L23_PC",
    "H21.29.195.11.01": "L5_PC",
    "H21.29.203.11.03.08": "L6_PC",
    "H21.29.203.11.91.04": "L6_PC",
    "H22.29.214.11.71.05": "L23_PC",
    "H22.29.219.11.72.01": "L4_PC",
}


def curate_morphology(data):
    if data.get("name", "") == "cylindrical_morphology_20.5398":
        data["subject"] = {
            "species": {
                "@id": "NCBITaxon:10090",
                "label": "Mus musculus",
            },
        }
    if data.get("name", "") in HUMAN_DATA_FIX:
        annotations = data["annotation"]
        if not isinstance(annotations, list):
            annotations = [annotations]
            data["annotations"] = annotations
        for annotation in annotations:
            if "MTypeAnnotation" in annotation["@type"]:
                annotation["hasBody"]["label"] = HUMAN_DATA_FIX[data["name"]]
                annotation["hasBody"]["@id"] = "INVALID"

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
            "label": "Felis catus",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "NCBITaxon:6619",
            "label": "Loligo pealeii",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "NCBITaxon:8400",
            "label": "Aquarana catesbeiana",
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


def curate_license(data):
    if data.get("@id") == "https://creativecommons.org/licenses/by/4.0":
        data["@id"] = "https://creativecommons.org/licenses/by/4.0/"
    return data


def curate_hierarchy_name(hierarchy_name):
    if hierarchy_name == "Isocortex, layer 1":
        return "Isocortex"
    return hierarchy_name


def curate_content_type(content_type):
    if content_type == "application/h5":
        return "application/x-hdf5"
    if content_type == "application/x-neuron-hoc":
        return "application/hoc"
    if content_type == "application/neuron-mod":
        return "application/mod"
    return content_type


def curate_distribution(distribution, project_context):
    if isinstance(distribution, list):
        return [curate_distribution(c, project_context) for c in distribution]
    distribution["encodingFormat"] = curate_content_type(distribution["encodingFormat"])
    assert distribution["@type"] == "DataDownload"
    assert distribution["contentSize"]["unitCode"] == "bytes"
    assert distribution["contentSize"]["value"] > 0
    assert distribution["digest"]["algorithm"] == "SHA-256"
    assert distribution["digest"]["value"] is not None
    if "atLocation" in distribution:
        if "@type" not in distribution["atLocation"]:
            L.error(f"Distribution {distribution} has no atLocation @type")

            distribution["atLocation"]["@type"] = "Location"
        assert distribution["atLocation"]["@type"] == "Location"
    else:
        msg = f"Distribution had not atLocation: {distribution}"
        L.warning(msg)
    return distribution
