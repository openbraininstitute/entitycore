import app.models.annotation
import app.models.base 
MAP_TYPES ={
    app.models.base.License: "License",
    app.models.annotation.MTypeAnnotationBody: "Class",
    app.models.annotation.ETypeAnnotationBody: "Class",
}

MAPPING_GLOBAL ={
        "creation_date": "_createdAt",
        "updated_date": "_updatedAt",
}
MAPPING_PER_TYPE ={
    app.models.base.License: {
        "name": "@id",
        "description": "description",
        "label": "label",
    },
    app.models.annotation.ETypeAnnotationBody: {
        "pref_label": "label",
        "definition": "definition",
    },
    app.models.annotation.MTypeAnnotationBody: {
        "pref_label": "label",
        "definition": "definition",
    }
}

def build_response_elem(elem):

    initial_dict = {
        "_constrainedBy": "https://bluebrain.github.io/nexus/schemas/unconstrained.json",
        "_deprecated": False,
        "_project": "https://openbluebrain.com/api/nexus/v1/projects/bbp/licenses",
        "_rev": 0,
        "_schemaProject": "https://openbluebrain.com/api/nexus/v1/projects/bbp/licenses",
        "_updatedBy": "https://openbluebrain.com/api/nexus/v1/realms/bbp/users/cgonzale",
    }
    mapping = {**MAPPING_PER_TYPE.get(elem.__class__,{}), **MAPPING_GLOBAL} 
    for key, value in mapping.items():
        initial_dict[value] = getattr(elem, key, "")
    initial_dict["@type"] = [MAP_TYPES[elem.__class__]] 
    initial_dict["@id"] = elem.legacy_id[0]
    return {
        "_id": elem.legacy_id[0],
        "_index": "dummy",
        "_score": 1.0,
        "_source": initial_dict,
    }

def build_response_body(elems):
    return {
        "hits": {
            "hits": [build_response_elem(elem) for elem in elems],
            "timed_out": False,
            "took": 2,
            "_shards": {"failed": 0, "skipped": 0, "successful": 6, "total": 6},
        }
    }