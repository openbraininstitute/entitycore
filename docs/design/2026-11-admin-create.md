# Admin create endpoints for entities and activities

- Status: Implemented
- Date: 2026-11-12
- Author: @GianlucaFicarelli
- Issues: [prod-platform-architecture#231](https://github.com/openbraininstitute/prod-platform-architecture/issues/231)
- Pull requests: [#765](https://github.com/openbraininstitute/entitycore/pull/765) (preparation), [#768](https://github.com/openbraininstitute/entitycore/pull/768) (admin routes ignoring the project headers), [#769](https://github.com/openbraininstitute/entitycore/pull/769) (admin create endpoints)

## Context

Entities and activities can only be created with the project-scoped user routes (`POST /<route>`), where the user must be a member of the project in the headers. The admin routes (`/admin/<route>`) cover read, update and delete only, so admins create entities in other projects with external scripts.

Admins aren't members of every project in Keycloak. The existing admin routes work in any project when no project headers are sent: `user_verified` accepts a request without headers, and the admin read, update, delete and asset operations take the project from the stored entity. Creation is different, because the project must come from the headers, and `user_verified` rejects headers naming a project that the user, service admins included, doesn't belong to. The admin router depends on `user_verified`, so the same 403 is returned to any admin request sending those headers, e.g. from a client configured with a project context.

In scope: an admin create endpoint for every entity and activity with `authorized_project_id`, and the changes needed to authorize admins in any project. Out of scope: associations (classifications and scientific artifact links), which register their admin routes by hand, left for a follow-up.

## Decision

### Authentication of the admin routes

The admin router depends on `user_with_service_admin_role`, which no longer goes through `user_verified`. Both call the same verification of the token with Keycloak; the admin dependency ignores the headers `virtual-lab-id` and `project-id`, then requires the service admin role. A user who isn't an admin gets "Service admin role required" on the admin routes, whatever the headers.

- The admin context describes only the caller: it has no `virtual_lab_id` and `project_id`. The project targeted by an admin request is part of the request (the payload of the admin create) or of the stored resource (read, update, delete and assets).
- The Keycloak cache key doesn't depend on the headers for the admin routes, so the same cached context is used for any headers.
- The user routes keep depending on `user_verified` at the router level, so admins have no special privilege there, also on the user routes restricted to admins (e.g. `POST /license`).
- A test checks that no admin or debug route depends on `user_verified`.
- The Keycloak result is cached also when the user isn't a member of the project. Its cache expiration considers the token expiration in that case too, so that a cached context never outlives the token.

### Admin create endpoints

`POST /admin/<route>` for every entity and activity, with the response of `POST /<route>`, and `expand` for entities.

- The body is the user create body with a required `authorized_project_id`. Each admin schema is a subclass of the create schema with `AuthorizedProjectIdMixin`, e.g. `CellMorphologyAdminCreate`, so that pyright checks the services and the OpenAPI docs show a named schema. A factory like `make_update_schema` was considered, but it would need `# pyright: ignore` in every service, and only one required field is added.
- The project is checked with virtual-lab-manager, using the existing admin client (`AdminVirtualLabClient.find_virtual_lab_by_project`). The services declare the body as `AdminCreateDep[<Entity>AdminCreate]`, a dependency like `FilterDep` that validates the body and then checks its project, so the check isn't repeated in every service. A test checks that every admin route with `authorized_project_id` in the body uses it. An unknown project returns 422 `PROJECT_NOT_FOUND`. virtual-lab-manager returns 403 also for unknown or deleted projects, so both 403 and 404 are treated as an unknown project, and logged as a warning, because a 403 can also mean that the admin token was rejected.
- With `APP_DISABLE_AUTH`, the admin client maps every project to `APP_DISABLE_AUTH_VIRTUAL_LAB_ID` without calling virtual-lab-manager, so any project is accepted.
- `load_db_model_from_pydantic` sets `authorized_project_id` from the context only when the context has a project, so the admin create takes it from the payload. The user create schemas don't declare the field, and the extra fields are ignored, so the user create still takes the project only from the headers.
- `created_by` and `updated_by` are the admin calling the endpoint.
- The create logic is the same as the user routes, including the checks that the referenced entities are public or in the same project as the created resource, and the database triggers.
- `admin_create_one` is added to the `AdminCrudService` protocol and registered by `register_default_admin_routes`, so all the admin routes have the same operations.
- The global resources define `admin_create_one = create_one`, because their user create already requires the admin role. The agents, publications and external URLs, whose user create is open to any user, define an `admin_create_one` with the admin role: an alias would make the admin route depend on the project membership.
- Contributions, derivations and measurement annotations have no project, and their admin create has no `authorized_project_id`. Contributions and measurement annotations reference an entity in any project. Derivations reference a generated entity in any project, and, as in the user create, a used entity public or in the project of the generated one; they keep the validation of the entity types and label.
- `create_one` and `admin_create_one` share the same create body, so that the admin create can't drift from the user create. The entities and activities use a private `_create_one`, accepting both contexts; the agents, publications and external URLs call `create_one`, because both use a `UserContext`.

### Admin contexts

No new context types: `AdminContextDep` returns `UserContext`, without project fields.

- `AdminContextWithProjectIdDep` and `user_with_service_admin_role_and_project_id` are removed. They were used only by `em_dense_reconstruction_dataset`, whose create moves to the admin routes.
- The admin read, update, delete and asset routes take the project from the stored entity, as before.
- The admin asset routes resolve the virtual lab from the project of the entity with virtual-lab-manager. When the project isn't found there, they return the same error as the user asset routes (422 `ASSET_VIRTUAL_LAB_ID_NOT_FOUND`) instead of 500. With `APP_DISABLE_AUTH`, they get `APP_DISABLE_AUTH_VIRTUAL_LAB_ID` from the same admin client.

### Resources with admin-only writes

`create_user_router` accepts the `operations` to register as user routes, all by default. Its service protocol requires only the read operations. `em_dense_reconstruction_dataset`, whose user create, update and delete already require the admin role, keeps only the user read routes; its create moves to `POST /admin/em-dense-reconstruction-dataset` with the behaviour above, with `authorized_project_id` in the body, and update and delete are available only through the existing admin routes.

## Alternatives considered

- **Authorizing service admins for any project in `user_verified`.** Simpler, but admins would also get access to any project on the user routes, where the project isn't validated with virtual-lab-manager.
- **The project in the headers, validated with virtual-lab-manager.** Implemented first in #768, then replaced. On the admin routes the headers named a target project instead of the project of the caller, so the admin context needed a project without membership, `is_authorized=False` for admins, a check of `virtual-lab-id` against the virtual lab of the project, and the `APP_DISABLE_AUTH` fallback on the admin path. In the body, the project is a required and documented field of the resource, and one admin token can create resources in any project without changing headers.
- **Copying the project of the payload into the admin context.** It needs no change of `router_create_one`, but the context would describe the target instead of the caller.
- **An optional protocol for admin create**, registered only by the routers supporting it. It avoids the aliases in the resources without a project, at the cost of two registration paths.
- **A flag to skip only the user create** (`include_create=False`). Doesn't cover update and delete, which have the same problem in `em_dense_reconstruction_dataset`.
- **Registering only the operations defined by the service module.** A missing or misnamed function would silently drop a route.
- **A parameter to skip the validation with virtual-lab-manager** (`?skip_project_validation=true`, with `virtual-lab-id` required). Deferred until there's a need for it.

## Consequences

- The admin routes ignore the project headers. Clients sending a project context, e.g. entitysdk, can keep sending it.
- The admin create body differs from the user create body by `authorized_project_id`.
- Admin create depends on virtual-lab-manager: it fails when the project is unknown or the service is unavailable.
- The error for a missing `project-id` on the user create endpoints says "The header project-id is required". `virtual-lab-id` was never needed: it's derived from the Keycloak groups, and a user who isn't a member is rejected earlier.
- On the user routes restricted to admins (e.g. `POST /license`), the token is verified twice per request: by `user_verified` with the project headers, and by `AdminContextDep` without them. Without project headers the second check is served by the Keycloak cache; with them, the first request per token makes two Keycloak calls, and the next ones are cached. This goes away when those writes move to the admin routes (see Follow-ups).
- `POST`, `PATCH` and `DELETE /em-dense-reconstruction-dataset` are removed. They were used only by migration scripts through entitysdk `register_entity`, which needs `admin=True` to use the admin route.
- The resources without a project get a `POST /admin/<route>` behaving as their user create.

## Follow-ups

- entitysdk: add `admin=True` to `register_entity`, to use `POST /admin/<route>` with `authorized_project_id` in the body. Needed by the admin create endpoints and by the move of the `em_dense_reconstruction_dataset` create.
- entitycore: move the writes restricted to admins of the global resources and agents to the admin routes, as for `em_dense_reconstruction_dataset`. The global resources (brain regions and hierarchies, etypes, mtypes, ion channels, licenses, measurement labels, roles, species, strains) keep only the user read routes. Consortia, organizations, persons, publications and external URLs keep the user read and create routes, and their update and delete move to the admin routes. Then `AdminContextDep` is used only on the admin routes, and the token is verified once per request. The old routes are removed without a transition period: no active client uses them, and entitysdk users switch to `admin=True`.
- Admin create for the associations (etype and mtype classifications, scientific artifact links).
- entitycore: a context type without the project fields for `AdminContextDep`. At runtime the admin context already has no project; the type would let pyright check it. Deferred because it touches most services and the shared query helpers, and it's better decided together with a consistent signature of the read helpers (`router_read_one` takes an optional context, `router_read_many` a project id and a flag).
- entitycore: an optional `authorized_project_id` in the body of the user create, possibly replacing the project headers there. Breaking change, out of scope. If both are accepted, a project in the body different from the project in the headers should be an error.
- virtual-lab-api: return 404 instead of 403 for an unknown project in `GET /virtual-labs/projects/{project_id}/virtual-lab` ([virtual-lab-api#218](https://github.com/openbraininstitute/virtual-lab-api/issues/218)).
- entitycore: public OpenAPI docs for the admin and debug routes, at `/admin/docs` and `/admin/openapi.json`, generated from the same app; `/openapi.json` keeps excluding them. Calling the endpoints still requires the service admin role.
