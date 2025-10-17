# Authentication

## General Rules

- All endpoints require authentication with a valid token, except for the [unauthenticated endpoints](#unauthenticated-endpoints).
- For authenticated endpoints:
  - If `virtual-lab-id` and `project-id` are provided in the request headers, they are validated with Keycloak using the given token.
  - If `virtual-lab-id` is provided without `project-id`, it is verified.
  - If `project-id` is provided without `virtual-lab-id`, authentication fails.
- Endpoints for [global resources](#endpoints-for-global-resources):
  - Do not require `virtual-lab-id` or `project-id`.
  - **Read** endpoints are accessible to all authenticated users.
  - **Write** endpoints require the user to be a member of the [service admin group](#service-admin-group).
- Endpoints for [project resources](#endpoints-for-project-resources):
  - **Read** endpoints do not require `virtual-lab-id` or `project-id`, but:
    - If neither is provided, only public resources are returned.
    - If both are provided, both public and private resources are returned.
  - **Write** endpoints require both `virtual-lab-id` and `project-id`.

## Service Admin Group

The special Keycloak group `/service/entitycore/admin` allows users to:

* call endpoints that modify global resources
* call admin endpoints

## Service Maintainer group

The special Keycloak group `/service/entitycore/maintainer` allows users to:

* update public entities within authorized projects
* delete public entities within authorized projects
* hard delete assets within authorized projects

## Caching

Requests to Keycloak are cached using a Time-aware Least Recently Used (TLRU) cache.
Similar to a TTL cache, this method assigns an expiration time to each item. However, in a TLRU cache, expiration time is determined individually for each item based on the token's expiration time, capped at the configured maximum TTL.

## Auditing

Auditing is not yet implemented but can be added later using information retrieved from Keycloak and stored in `UserContext`.

## Endpoints for Global Resources

- `/brain-region`
- `/cell-composition`
- `/license`
- `/mtype`
- `/organization`
- `/person`
- `/role`
- `/species`
- `/strain`

## Endpoints for Project Resources

- `/assets`
- `/contribution`
- `/emodel`
- `/experimental-bouton-density`
- `/experimental-neuron-density`
- `/experimental-synapses-per-connection`
- `/cell-morphology`
- `/morphology-feature-annotation`
- `/single-neuron-simulation`

## Unauthenticated endpoints

- `/health`
- `/version`
- `/docs`
