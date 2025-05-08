"""Web api."""

from fastapi import APIRouter, Depends

from app.dependencies.auth import user_verified
from app.routers import (
    asset,
    brain_region,
    brain_region_hierarchy_name,
    cell_composition,
    contribution,
    electrical_cell_recording,
    emodel,
    experimental_bouton_density,
    experimental_neuron_density,
    experimental_synapses_per_connection,
    ion_channel_model,
    license,
    measurement_annotation,
    memodel,
    morphology,
    mtype,
    organization,
    person,
    role,
    root,
    single_neuron_simulation,
    single_neuron_synaptome,
    single_neuron_synaptome_simulation,
    species,
    strain,
    subject,
)

router = APIRouter()
router.include_router(root.router)
authenticated_routers = [
    asset.router,
    brain_region.router,
    brain_region_hierarchy_name.router,
    cell_composition.router,
    contribution.router,
    electrical_cell_recording.router,
    emodel.router,
    experimental_bouton_density.router,
    experimental_neuron_density.router,
    experimental_synapses_per_connection.router,
    license.router,
    measurement_annotation.router,
    memodel.router,
    morphology.router,
    mtype.router,
    organization.router,
    person.router,
    role.router,
    single_neuron_simulation.router,
    single_neuron_synaptome.router,
    single_neuron_synaptome_simulation.router,
    species.router,
    strain.router,
    subject.router,
    ion_channel_model.router,
]
for r in authenticated_routers:
    router.include_router(r, dependencies=[Depends(user_verified)])
