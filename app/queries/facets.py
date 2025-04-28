from app.db.model import Agent, BrainRegion, ETypeClass, MEModel, MTypeClass, Species, Strain
from app.dependencies.common import FacetQueryParams

brain_region: dict[str, FacetQueryParams] = {
    "brain_region": {"id": BrainRegion.id, "label": BrainRegion.name},
}
creator: dict[str, FacetQueryParams] = {
    "createdBy": {
        "id": Agent.id,
        "label": Agent.pref_label,
        "type": Agent.type,
    },
    "updatedBy": {
        "id": Agent.id,
        "label": Agent.pref_label,
        "type": Agent.type,
    },
}
contribution: dict[str, FacetQueryParams] = {
    "contribution": {
        "id": Agent.id,
        "label": Agent.pref_label,
        "type": Agent.type,
    }
}
etype: dict[str, FacetQueryParams] = {
    "etype": {"id": ETypeClass.id, "label": ETypeClass.pref_label},
}
mtype: dict[str, FacetQueryParams] = {
    "mtype": {"id": MTypeClass.id, "label": MTypeClass.pref_label},
}
memodel: dict[str, FacetQueryParams] = {
    "me_model": {"id": MEModel.id, "label": MEModel.name},
}
species: dict[str, FacetQueryParams] = {
    "species": {
        "id": Species.id,
        "label": Species.name,
    }
}
strain: dict[str, FacetQueryParams] = {"strain": {"id": Strain.id, "label": Strain.name}}

synaptic_pathway: dict[str, FacetQueryParams] = {
    "pre_mtype": mtype["mtype"],
    "post_mtype": mtype["mtype"],
    "pre_region": brain_region["brain_region"],
    "post_region": brain_region["brain_region"],
}
