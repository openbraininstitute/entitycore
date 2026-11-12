# Admin create endpoints for entities and activities

- Status: Accepted
- Date: 2026-11-12
- Author: @GianlucaFicarelli
- Issues: [prod-platform-architecture#231](https://github.com/openbraininstitute/prod-platform-architecture/issues/231)
- Pull requests: preparation (this PR), admin create endpoints (follow-up)

## Context

Entities and activities can only be created with the project-scoped user routes (`POST /<route>`), where the user must be a member of the project in the headers. The admin routes (`/admin/<route>`) cover read, update and delete only, so admins create entities in other projects with external scripts.

Admins aren't members of every project in Keycloak, and today they can't use the admin routes with a project they don't belong to: `user_verified` checks the membership of the project in the headers for every request, admins included, and the admin router depends on it.

In scope: an admin create endpoint for every entity and activity with `authorized_project_id`, and the changes needed to authorize admins in any project. Out of scope: associations (classifications and scientific artifact links), which register their admin routes by hand, left for a follow-up.

## Decision

### Authentication of the admin routes

The admin router depends on `user_with_service_admin_role`, which no longer goes through `user_verified`. Both call the same verification of the token with Keycloak; the admin dependency accepts a service admin when the only failure is the membership of the project in the headers.

- When only `project-id` is given and the admin isn't a member, `virtual_lab_id` stays `None` in the context, because it can't be derived from the Keycloak groups.
- The user routes keep depending on `user_verified` at the router level, so admins have no special privilege there, also on the user routes restricted to admins (e.g. `POST /license`).
- A test checks that no admin or debug route depends on `user_verified`.
- The Keycloak result is cached also when the user isn't a member of the project. Its cache expiration now considers the token expiration in that case too, so that an expired token can't be accepted on the admin routes from the cache.

### Admin create endpoints

`POST /admin/<route>` for every entity and activity, with the same body and response as `POST /<route>`, and `expand` for entities.

- `project-id` is required, `virtual-lab-id` is optional, as in the user routes.
- The project is checked with virtual-lab-manager, using the existing admin client (`AdminVirtualLabClient.get_virtual_lab_by_project`). An unknown project is rejected; when `virtual-lab-id` is given, it must be the virtual lab of the project.
- `?skip_project_validation=true` skips the call to virtual-lab-manager, and with it the check of `virtual-lab-id`. It is available to service admins only, since the admin router requires the role.
- `created_by` and `updated_by` are the admin calling the endpoint.
- The create logic is the same as the user routes, including the checks that the referenced entities are public or in the same project, and the database triggers.
- `AdminContextWithProjectIdDep` is replaced by a single dependency with this behaviour; it's used only by `em_dense_reconstruction_dataset` today.
- `admin_create_one` is added to the `AdminCrudService` protocol and registered by `register_default_admin_routes`. The resources without a project (global resources, agents, publications, external URLs) define `admin_create_one = create_one`: same behaviour as their user create, which is already admin-only or unrestricted, so all the admin routes have the same operations.
- Services whose `create_one` has extra logic share it with `admin_create_one` through a private function.

### Resources with admin-only writes

`create_user_router` accepts the `operations` to register as user routes, all by default. `em_dense_reconstruction_dataset`, whose user create, update and delete already require the admin role, keeps only the user read routes; its create moves to `POST /admin/em-dense-reconstruction-dataset` with the behaviour above, and update and delete are available only through the existing admin routes.

## Alternatives considered

- **Authorizing service admins for any project in `user_verified`.** Simpler, but admins would also get access to any project on the user routes, where the project isn't validated with virtual-lab-manager.
- **The project in the body instead of the headers.** Inconsistent with the other create endpoints and with the asset upload, which uses the project of the entity.
- **An optional protocol for admin create**, registered only by the routers supporting it. It avoids the aliases in the resources without a project, at the cost of two registration paths.
- **A flag to skip only the user create** (`include_create=False`). Doesn't cover update and delete, which have the same problem in `em_dense_reconstruction_dataset`.
- **Registering only the operations defined by the service module.** A missing or misnamed function would silently drop a route.

## Consequences

- Service admins can use the admin routes with the headers of a project they don't belong to.
- On the user routes restricted to admins (e.g. `POST /license`), the token is verified twice per request; the second time is served by the Keycloak cache. This goes away when those writes move to the admin routes (see Follow-ups).
- `POST`, `PATCH` and `DELETE /em-dense-reconstruction-dataset` are removed. They were used only by migration scripts through entitysdk `register_entity`, which needs `admin=True` to use the admin route.
- The resources without a project get a `POST /admin/<route>` behaving as their user create.

## Follow-ups

- entitysdk: add `admin=True` to `register_entity`, to use `POST /admin/<route>`. Needed by the admin create endpoints and by the move of the `em_dense_reconstruction_dataset` create.
- entitycore: move the writes restricted to admins of the global resources and agents to the admin routes, as for `em_dense_reconstruction_dataset`. The global resources (brain regions and hierarchies, etypes, mtypes, ion channels, licenses, measurement labels, roles, species, strains) keep only the user read routes. Consortia, organizations, persons, publications and external URLs keep the user read and create routes, and their update and delete move to the admin routes. Then `AdminContextDep` is used only on the admin routes, and the token is verified once per request. The old routes are removed without a transition period: no active client uses them, and entitysdk users switch to `admin=True`.
- Admin create for the associations (etype and mtype classifications, scientific artifact links).
