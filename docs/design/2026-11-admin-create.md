# Admin create endpoints for entities and activities

- Status: Implemented
- Date: 2026-11-12
- Author: @GianlucaFicarelli
- Issues: [prod-platform-architecture#231](https://github.com/openbraininstitute/prod-platform-architecture/issues/231)
- Pull requests: [#765](https://github.com/openbraininstitute/entitycore/pull/765) (preparation), [#768](https://github.com/openbraininstitute/entitycore/pull/768) (admin project context), [#769](https://github.com/openbraininstitute/entitycore/pull/769) (admin create endpoints)

## Context

Entities and activities can only be created with the project-scoped user routes (`POST /<route>`), where the user must be a member of the project in the headers. The admin routes (`/admin/<route>`) cover read, update and delete only, so admins create entities in other projects with external scripts.

Admins aren't members of every project in Keycloak. The existing admin routes work in any project when no project headers are sent: `user_verified` accepts a request without headers, and the admin read, update, delete and asset operations take the project from the stored entity. Creation is different, because the project must come from the headers, and `user_verified` rejects headers naming a project that the user, service admins included, doesn't belong to. The admin router depends on `user_verified`, so the same 403 is returned to any admin request sending those headers, e.g. from a client configured with a project context.

In scope: an admin create endpoint for every entity and activity with `authorized_project_id`, and the changes needed to authorize admins in any project. Out of scope: associations (classifications and scientific artifact links), which register their admin routes by hand, left for a follow-up.

## Decision

### Authentication of the admin routes

The admin router depends on `user_with_service_admin_role`, which no longer goes through `user_verified`. Both call the same verification of the token with Keycloak; the admin dependency skips the membership of the project in the headers, then requires the service admin role. A user who is neither a member nor an admin gets "Service admin role required" on the admin routes.

- When only `project-id` is given and the admin isn't a member, `virtual_lab_id` stays `None` in the context, because it can't be derived from the Keycloak groups. The admin create endpoints remove this case (see Admin contexts).
- The user routes keep depending on `user_verified` at the router level, so admins have no special privilege there, also on the user routes restricted to admins (e.g. `POST /license`).
- A test checks that no admin or debug route depends on `user_verified`.
- The Keycloak result is cached also when the user isn't a member of the project. Its cache expiration now considers the token expiration in that case too, so that an expired token can't be accepted on the admin routes from the cache.

### Admin create endpoints

`POST /admin/<route>` for every entity and activity, with the same body and response as `POST /<route>`, and `expand` for entities.

- `project-id` is required, `virtual-lab-id` is optional, as in the user routes.
- The project is checked with virtual-lab-manager, using the existing admin client (`AdminVirtualLabClient.find_virtual_lab_by_project`). An unknown project is rejected; when `virtual-lab-id` is given, it must be the virtual lab of the project. virtual-lab-manager returns 403 also for unknown or deleted projects, so both 403 and 404 are treated as an unknown project.
- With `APP_DISABLE_AUTH`, virtual-lab-manager isn't called: the virtual lab is taken from `virtual-lab-id`, or `APP_DISABLE_AUTH_VIRTUAL_LAB_ID` when only `project-id` is given. The user routes use the same fallback.
- `created_by` and `updated_by` are the admin calling the endpoint.
- The create logic is the same as the user routes, including the checks that the referenced entities are public or in the same project, and the database triggers.
- `admin_create_one` is added to the `AdminCrudService` protocol and registered by `register_default_admin_routes`, so all the admin routes have the same operations.
- The global resources define `admin_create_one = create_one`, because their user create already requires the admin role. The agents, publications and external URLs, whose user create is open to any user, define an `admin_create_one` with the admin role: an alias would make the admin route depend on the project membership. Both ignore the project headers.
- Contributions, derivations and measurement annotations have no project, but their create checks the referenced entities against the project in the headers, so their `admin_create_one` validates the project as the entities and activities do.
- Services whose `create_one` has extra logic share it with `admin_create_one` through a private function.

### Admin contexts

No new context types: the admin dependencies return the existing schemas, and differ from the user ones only in the checks done before returning.

- `AdminContextWithProjectIdDep` returns `UserContextWithProjectId`, with `virtual_lab_id` and `project_id` always set, as for the user create. It checks the admin role and validates the project as described above, instead of the Keycloak membership. It keeps its name and replaces the current implementation, used only by `em_dense_reconstruction_dataset`. It's used only by the admin create of the entities, activities, contributions, derivations and measurement annotations.
- `AdminContextDep` is unchanged. The admin read, update, delete and asset routes take the project from the stored entity, and ignore the project headers. Returning a context without the project fields is deferred (see Follow-ups): the admin create doesn't need it.
- The admin asset routes keep resolving the virtual lab from the project of the entity with virtual-lab-manager. When the project isn't found there, they return the same error as the user asset routes (422 `ASSET_VIRTUAL_LAB_ID_NOT_FOUND`) instead of 500.
- A separate admin type with the same fields as `UserContextWithProjectId` was considered and not needed: no code receiving it relies on the project membership.

### Resources with admin-only writes

`create_user_router` accepts the `operations` to register as user routes, all by default. Its service protocol requires only the read operations. `em_dense_reconstruction_dataset`, whose user create, update and delete already require the admin role, keeps only the user read routes; its create moves to `POST /admin/em-dense-reconstruction-dataset` with the behaviour above, and update and delete are available only through the existing admin routes.

## Alternatives considered

- **Authorizing service admins for any project in `user_verified`.** Simpler, but admins would also get access to any project on the user routes, where the project isn't validated with virtual-lab-manager.
- **The project in the body instead of the headers.** Inconsistent with the other create endpoints and with the asset upload, which uses the project of the entity.
- **An optional protocol for admin create**, registered only by the routers supporting it. It avoids the aliases in the resources without a project, at the cost of two registration paths.
- **A flag to skip only the user create** (`include_create=False`). Doesn't cover update and delete, which have the same problem in `em_dense_reconstruction_dataset`.
- **Registering only the operations defined by the service module.** A missing or misnamed function would silently drop a route.
- **A parameter to skip the validation with virtual-lab-manager** (`?skip_project_validation=true`, with `virtual-lab-id` required). Deferred until there's a need for it.

## Consequences

- Service admins can send the headers of a project they don't belong to on the admin routes. Admin create needs this. The other admin routes keep ignoring the headers.
- Admin create depends on virtual-lab-manager: it fails when the project is unknown or the service is unavailable.
- The error for a missing `project-id` on the create endpoints says "The header project-id is required". On the user routes `virtual-lab-id` was never needed: it's derived from the Keycloak groups, and a user who isn't a member is rejected earlier.
- On the user routes restricted to admins (e.g. `POST /license`), the token is verified twice per request; the second time is served by the Keycloak cache. This goes away when those writes move to the admin routes (see Follow-ups).
- `POST`, `PATCH` and `DELETE /em-dense-reconstruction-dataset` are removed. They were used only by migration scripts through entitysdk `register_entity`, which needs `admin=True` to use the admin route.
- The resources without a project get a `POST /admin/<route>` behaving as their user create.

## Follow-ups

- entitysdk: add `admin=True` to `register_entity`, to use `POST /admin/<route>`. Needed by the admin create endpoints and by the move of the `em_dense_reconstruction_dataset` create.
- entitycore: move the writes restricted to admins of the global resources and agents to the admin routes, as for `em_dense_reconstruction_dataset`. The global resources (brain regions and hierarchies, etypes, mtypes, ion channels, licenses, measurement labels, roles, species, strains) keep only the user read routes. Consortia, organizations, persons, publications and external URLs keep the user read and create routes, and their update and delete move to the admin routes. Then `AdminContextDep` is used only on the admin routes, and the token is verified once per request. The old routes are removed without a transition period: no active client uses them, and entitysdk users switch to `admin=True`.
- Admin create for the associations (etype and mtype classifications, scientific artifact links).
- entitycore: `AdminContextDep` returns a context without the project fields, so that the admin read, update, delete and asset routes can't use the project headers by mistake. Deferred from the admin create because it touches most services and the shared query helpers, and it's better decided together with a consistent signature of the read helpers (`router_read_one` takes an optional context, `router_read_many` a project id and a flag).
- virtual-lab-api: return 404 instead of 403 for an unknown project in `GET /virtual-labs/projects/{project_id}/virtual-lab` ([virtual-lab-api#218](https://github.com/openbraininstitute/virtual-lab-api/issues/218)).
- entitycore: public OpenAPI docs for the admin and debug routes, at `/admin/docs` and `/admin/openapi.json`, generated from the same app; `/openapi.json` keeps excluding them. Calling the endpoints still requires the service admin role.
