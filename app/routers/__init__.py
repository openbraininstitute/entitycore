"""Web api."""

from fastapi import APIRouter, Depends

from app.dependencies.auth import user_verified
from app.routers import (
    asset,
    brain_atlas,
    brain_region,
    brain_region_hierarchy,
    cell_composition,
    contribution,
    electrical_cell_recording,
    emodel,
    etype,
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
    validation_result,
)

router = APIRouter()
router.include_router(root.router)
authenticated_routers = [
    asset.router,
    brain_atlas.router,
    brain_region.router,
    brain_region_hierarchy.router,
    cell_composition.router,
    contribution.router,
    electrical_cell_recording.router,
    emodel.router,
    etype.router,
    experimental_bouton_density.router,
    experimental_neuron_density.router,
    experimental_synapses_per_connection.router,
    ion_channel_model.router,
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
    validation_result.router,
]
for r in authenticated_routers:
    router.include_router(r, dependencies=[Depends(user_verified)])
