"""Web api."""

from fastapi import APIRouter

from app.routers import (
    asset,
    brain_region,
    contribution,
    experimental_bouton_density,
    experimental_neuron_density,
    experimental_synapses_per_connection,
    license,
    morphology,
    morphology_feature_annotation,
    organization,
    person,
    role,
    root,
    species,
    strain,
)
from app.routers.legacy import _search, files, resources, sbo

router = APIRouter()
router.include_router(root.router)
router.include_router(asset.router)
router.include_router(brain_region.router)
router.include_router(contribution.router)
router.include_router(experimental_bouton_density.router)
router.include_router(experimental_neuron_density.router)
router.include_router(experimental_synapses_per_connection.router)
router.include_router(license.router)
router.include_router(morphology.router)
router.include_router(morphology_feature_annotation.router)
router.include_router(organization.router)
router.include_router(person.router)
router.include_router(role.router)
router.include_router(species.router)
router.include_router(strain.router)

# legacy routes
router.include_router(_search.router)
router.include_router(sbo.router)
router.include_router(resources.router)
router.include_router(files.router)
