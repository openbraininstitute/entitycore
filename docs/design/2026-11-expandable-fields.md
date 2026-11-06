# Expandable fields in read responses

- Status: Implemented
- Date: 2026-11-03
- Author: @GianlucaFicarelli
- Issues: [prod-platform-architecture#232](https://github.com/openbraininstitute/prod-platform-architecture/issues/232)
- Pull requests: [#751](https://github.com/openbraininstitute/entitycore/pull/751)

## Context

Some fields of the read responses should be returned only when the client asks for them: optional or heavy data, such as JSONB metadata columns or large nested relationships, that `read_many` should not load by default. The need came up when storing summary data of electrical cell recordings; that case was solved with an asset (`recording_summary`, [#750](https://github.com/openbraininstitute/entitycore/pull/750)), so this design is not tied to a specific field.

entitycore already has two opt-in fields, implemented in different ways:

- **Derivations**, `expand=generated_from_derivations[:<derivation_type>]` and `expand=used_by_derivations[:<derivation_type>]` (`app/queries/expand.py`). `Entity` has view-only relationships (`derivations_as_generated`, `derivations_as_used`) plus properties that return `None` when the relationship is not loaded. Not requested, the fields are `null`.
- **Measurement annotation**, `expand=measurement_annotation` on cell morphologies and EM cell meshes. The service loads the relationship and switches the response to a second schema (`CellMorphologyAnnotationExpandedRead`, `EMCellMeshAnnotationExpandedRead`). Not requested, the field is absent.

The first needs code in the SQLAlchemy models for each field; the second needs a Read schema for each combination of optional fields. Neither supports nested objects.

In scope: a generic mechanism for columns and relationships at any nesting level, and the migration of the two existing fields. Out of scope: limiting the default fields (sparse fieldsets), and the length of GET query strings (see Consequences).

## Decision

### API

The existing `expand` query parameter is kept and generalized.

- A value is a path relative to the returned item, with `.` between levels and an optional `:qualifier` on the last segment: `summary`, `stimuli.summary`, `generated_from_derivations:circuit_extraction`. The same paths work for every endpoint returning the Read schema: `read_one`, `read_many` (no `data.` prefix), create (`POST`) and update (`PATCH`), user and admin. `=` stays reserved for future keyed qualifiers.
- Repeat `expand` to request several paths. A path implies its expandable ancestors: `a.b` also loads `a` if `a` is expandable.
- An expandable field that is not requested is **absent** from the response. Requested, a list is `[]` when empty, and a single value is `null` when it has no value. As in GraphQL, the client gets what it selects.
- Invalid paths return 422 with the allowed values. The allowed values of each endpoint are listed in OpenAPI.

Example, with a hypothetical deferred JSONB column `summary` on the stimuli of a recording:

```
GET /electrical-cell-recording/{id}?expand=stimuli.summary
```

### Marking a field as expandable

Fields are marked in the Read schema, which stays unique per entity. The SQLAlchemy models need no per-field code beyond the column or relationship itself (e.g. `deferred=True` for a heavy column).

An expandable field has the marker and the Pydantic `MISSING` sentinel as default. Pydantic omits fields whose value is `MISSING` from the output, so no custom serializer is needed.

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class Expandable:
    """Marks a read-schema field as returned only when requested with `expand`.

    Args:
        loader: name of the custom loader, for fields needing more than a loader strategy.
    """

    loader: ExpandLoaderName | None = None


class DerivationReadMixin(ExpandableSchema):
    generated_from_derivations: Annotated[
        list[GeneratedDerivationRead] | MISSING, Expandable(loader="generated_from_derivations")
    ] = MISSING


class SomeRead(ExpandableSchema, ...):
    summary: Annotated[dict | None | MISSING, Expandable()] = MISSING
```

The ORM attribute of a field has the name of the field, or its `validation_alias` when they differ, as for any field read from the ORM.

`None` is part of the type only for single values (a nullable column or a single-object relationship). A list is `[]` when empty, so list fields are `list[X] | MISSING`.

When a schema class is created, its expandable fields are collected, and four rules are checked: the default must be `MISSING`, a list field must not allow `None`, a `validation_alias` must be a string, and a class with expandable fields must inherit from `ExpandableSchema`. The marker and its helpers are in `app/schemas/expand.py`; `Schema` and `ExpandableSchema` in `app/schemas/base.py` use them.

The schema only says which fields are expandable; how they are loaded is decided on the query side, as for the rest of the queries. Most fields are loaded with a loader strategy (see Loading). The fields needing more, e.g. nested relationships of the related objects or qualifiers, name a custom loader in their marker (`Expandable(loader="generated_from_derivations")`), named after the field it was written for. The names are a `Literal` type (`ExpandLoaderName` in `app/schemas/expand.py`), and `CUSTOM_LOADERS` in `app/queries/expand_loaders.py` maps each name to the loader and the qualifiers it accepts: the derivations (qualified by the derivation types) and `measurement_annotation`. Pyright checks the names on both sides, and a test checks that the names, the dict keys and the names used by the fields are the same.

### Loading

The SQLAlchemy loaded state is the source of truth: the query loads what the requested paths need, and serialization includes an expandable field only if its attribute is loaded. No request information has to reach Pydantic, and nesting works because nested schemas behave the same way.

A generic `apply_expand(query, db_model_class, schema_class, expand, context=...)` replaces `apply_derivation_expand` in `router_read_one` and `router_read_many`, and is also applied by `router_create_one` and `router_update_one` (see Create and update). At startup, the schema fields and the mapper are walked in parallel to build a plan for each allowed path: the chain of loader options from the root. The same plans give the allowed values (see Allowed values), so the enum and the loading can't disagree. Each segment uses:

| Segment | Option |
|---|---|
| column (last segment only) | `undefer` |
| relationship, intermediate, not expandable | `defaultload` (keeps the strategy chosen by the service) |
| relationship, expandable | `selectinload` |
| field with a custom loader | the options built by the loader (derivations: `selectinload` with the derivation types, `joinedload` of the other entity) |

The services keep ending their loader options with `raiseload("*")`, and the specific options added by `apply_expand` override it, as today for derivations. An intermediate segment must be a field the service always loads, or an expandable field; otherwise the request fails at serialization, which signals a missing load in the service.

The `raiseload("*")` of the service only covers the attributes of the returned item. Below an expandable relationship loaded by `apply_expand`, a `raiseload("*")` is added too, so that the nested relationships of its Read schema raise instead of being lazy loaded once per object; they must be loaded by a custom loader (e.g. `measurement_annotation` loads its kinds, items and labels).

First version restrictions: polymorphic relationships needing `of_type` (e.g. `Contribution.agent`) are not expandable through nested paths, a field with a custom loader is always the last segment of a path, and qualifiers are only accepted by fields with a custom loader.

### Create and update

Create and update responses follow the same rule as reads: expandable fields are absent unless requested with `expand`. Without this, the two would differ: after a create, `router_create_one` refreshes the instance, and the refresh leaves deferred columns unloaded, so they are absent; after a PATCH, the columns it sets stay loaded, so they would be returned.

- Create: when the service gives loader options, `router_create_one` already reads the new instance again with them, as `router_read_one` does; `apply_expand` is added to that query. When it only refreshes the instance and `expand` is given, it reads the instance again with the expand options.
- Update: `apply_expand` is added to the query that loads the instance. Before validation, `router_update_one` expires the expandable attributes that are loaded but not requested, e.g. a column set by the PATCH, together with the attributes it already expires. Expiring only marks them as unloaded and runs no query.

Without `expand`, create and update run the same queries as today.

### Validation and serialization

`ExpandableSchema(Schema)` has a wrap `model_validator`. When the input is an ORM instance, the handler receives a thin proxy that:

- raises `AttributeError` for the ORM attributes of the expandable fields that are in `sa.inspect(instance).unloaded`, so Pydantic uses the `MISSING` default;
- delegates everything else to the instance.

The unloaded attribute is never accessed, so there is no lazy load and `raiseload` is not triggered. Non-expandable attributes are read as today, so a relationship that the service forgot to load still raises. `validation_alias` keeps working, because the proxy is read with `from_attributes` like the instance; an expandable field accepts only a string alias, which names the attribute to hide.

The validator is only on `ExpandableSchema`, not on the base `Schema`, because a Python validator on every class adds a call for each nested object (contributions, assets, brain region, ...). Serialization needs nothing: `MISSING` is omitted by Pydantic, in nested objects and lists too, and it stays omitted if FastAPI validates the response again.

### Prototype

A throwaway prototype checked the design against a local copy of the production database, with SQLAlchemy 2.1, Pydantic 2.14 and FastAPI 0.161:

- `undefer` of deferred columns declared on `entity`, `scientific_artifact` and `cell_morphology` works through the `CellMorphology` subclass, in a single query.
- `defaultload(rel).undefer(col)` loads a nested column while keeping the service's loading strategy for `rel`. `selectinload` works for an expandable relationship whose field name differs from the ORM attribute.
- The proxy works with real instances, nested, in lists and with `AliasPath`. A non-expandable relationship that isn't loaded still fails, with a validation error that wraps the `lazy='raise'` error.
- Through a route, fields that aren't requested are absent and requested ones are present, also when the route returns the ORM object directly.
- The generated `/openapi.json` is the same as on `main` with the derivation fields declared as `list[...] | None | MISSING`, compared field by field with list order normalized. FastAPI doesn't put defaults in response schemas, so `None` and `MISSING` produce the same field schema. Dropping `None` from the list fields, as proposed, changes their schema from "array or null" to "array".
- `Session.refresh()` doesn't load deferred columns; `refresh(instance, attribute_names=[...])` does.
- pyright 1.1.414 accepts `X | None | MISSING` and narrowing with `is MISSING`.

Validation and serialization of 100 cell morphologies, median of 50 runs on a laptop:

| Variant | Validation | Response validation + JSON |
|---|---|---|
| `main` | 4.9 ms | 1.95 ms |
| validator and wrap serializer on the base `Schema` | 5.3 ms | 4.8 ms |
| validator on the base `Schema`, `MISSING` | 5.5 ms | 2.1 ms |
| validator on `ExpandableSchema` only, `MISSING` (proposed) | 5.0 ms | 2.1 ms |

For comparison, a whole warm `read_many` of 30 cell morphologies takes about 60 ms on the same machine. Absolute times on Fargate will be higher, but the ratios between the variants should be similar.

### Allowed values

The allowed paths of an endpoint are computed from its Read schema: each expandable field gives a path, and nested schemas (including `list[...]` and `X | None`) are walked with a prefix, with a depth limit and a cycle guard. Fields with qualifiers add one value per qualifier.

They are exposed as a `StrEnum` per Read schema, named `<Schema>Expand` (e.g. `CircuitReadExpand`), as `EntityExpand` and `MeasurableEntityExpand` today, so FastAPI returns 422 for invalid values and OpenAPI lists them. One dependency per Read schema (`expand_query(CellMorphologyRead, CellMorphology)` in `app/dependencies/common.py`) replaces `ExpandDep` and `MeasurableEntityExpandDep`, is added to the read, create and update routes, and passes the parsed paths to the services, so a future body-based read endpoint can reuse them.

Today `EntityExpand` has 20 values (2 directions, each bare or with one of 9 derivation types). Nested objects mostly use `Nested*Read` schemas without derivations, so the enums should stay close to this size. If nested paths and qualifiers make them too large, the dependency can switch to validated strings without changing the API.

### Authorization of expanded entities

Expanding a relationship to other entities must not return entities that the user cannot read ([prod-platform-architecture#229](https://github.com/openbraininstitute/prod-platform-architecture/issues/229)). `apply_expand` receives an `ExpandContext`, built by the router helpers with the projects that authorized the returned item (public or in the project for reads, the projects of the write check for updates), or without filter in the admin endpoints. The custom loaders receive it, and the derivation loader keeps only the derivations whose other entity is public or in those projects. Relationships to entities without such a loader are not expandable.

### Existing fields

Both are migrated in the same pull request as the mechanism, to check that it covers the existing cases.

- Derivations: marked in `DerivationReadMixin` and loaded by custom loaders; the two properties on `Entity` are removed, and its relationships are renamed after the fields.
- `measurement_annotation`: marked in the morphology and EM cell mesh Read schemas, and loaded by a custom loader; the `*AnnotationExpandedRead` schemas are removed.

## Alternatives considered

- **A Read schema per combination of optional fields**, as for `measurement_annotation`. The number of schemas grows with the combinations, and every service has to choose between them.
- **An ORM attribute plus a load-aware property per field**, as for derivations. Per-field code in the models, and the field is `null` instead of absent.
- **A wrap `model_serializer` on the base `Schema`** removing the expandable fields not in `model_fields_set`, with `None` as default. It works, but it makes every nested object go through Python during serialization: the JSON output of `read_many` takes 2.5 times longer (see Prototype). Its return must also be left unannotated: with `-> Any` the serialization schema, and so OpenAPI, becomes empty.
- **Treating every unloaded attribute as absent.** It would remove the `raiseload("*")` safety net: a relationship that a service forgot to load would silently disappear from the response.
- **`response_model_exclude_unset=True` on the routes.** It applies to all the fields of the route, not only the expandable ones.
- **Passing the requested paths to Pydantic in the validation context.** It needs plumbing through every `model_validate` call and nested model, while the loaded state already carries the information.
- **Allowed values as validated strings instead of enums.** Avoids large enums if nested paths multiply with qualifiers, at the cost of custom 422 errors and a hand-written OpenAPI description. Kept as a fallback if the enums get too large.
- **A placeholder when a related object is not expanded**, either the id in place of the object (as in the Stripe API) or a separate `<name>_id` field. The first gives the key two types (a string or an object) for typed clients and OpenAPI; the second adds a second representation of the same relationship. A field whose id is always needed stays non-expandable and always loaded.
- **Never returning expandable fields in create and update responses**, by expiring them before validation. Simpler, but the same Read schema would then follow different rules depending on the endpoint. The Stripe API also accepts `expand` on create and update requests.
- **Custom loaders in the schema marker**, as callables. The schemas would contain SQLAlchemy loading code, and moving it to `app/queries` would create an import cycle.
- **A registry of custom loaders matched by ORM class and attribute name.** The match is implicit: the field doesn't show it has a custom loader, and a loader for a single class would depend on the order of the registry.
- **Other parameter names.** `include` in JSON:API selects related resources to add as separate documents, not fields; `fields` in JSON:API restricts the default fields, the opposite direction, and could be added later independently; GraphQL would be a full query language, not justified here. `expand` is already public and has the same meaning as in the Stripe API.

## Consequences

- `generated_from_derivations` and `used_by_derivations` are **absent** instead of `null` when not expanded, and never `null` when expanded; their OpenAPI type becomes a plain array. entitysdk already defaults them to `None`, which accepts both; other clients reading these keys must handle the absence.
- The `*AnnotationExpandedRead` schemas disappear from OpenAPI; the responses are unchanged. Clients generated from OpenAPI may notice.
- `docs/API.md` ("Expanding derivations", renamed "Expanding optional fields") is updated to describe the generic parameter.
- A field is serialized when its attribute is loaded, even if not requested, e.g. an object already loaded in the same session by a read. This is harmless and documented. Create and update avoid it for their own instance (see Create and update).
- Every create and update route gets an `expand` parameter, user and admin.
- `/openapi.json` grows from 1.55 MB to 1.64 MB: the `expand` parameter is on 150 operations instead of 74, and the 38 expand enums, one per Read schema, take about 40 KB, most with the same 20 values. The parameter description is kept short, since it's repeated on every operation; the full rules are in `docs/API.md`.
- The validator adds about 2% to the validation of the entity Read schemas, which all have expandable fields because of the derivations (see Prototype). Measured end to end on the implementation, the read endpoints take the same time as before and run the same SQL queries.
- In Python code, an expandable field of a Read schema can be `MISSING`; code reading these fields must check it (`is MISSING`). This concerns entitycore only: clients see an absent key.
- `pydantic>=2.14` is required (`MISSING` is stable from that version); the lock file already has 2.14.1.
- Expand paths are short, but the query string is limited (16 KB request line on the AWS load balancer). The limit is a concern mainly for long `id__in` lists, which clients should split. Parsing `expand` in a dependency keeps the design compatible with a future body-based read endpoint.

## Follow-ups

- entitycore: limit the derivation-type qualifiers of each `expand` enum to the types allowed for the entity type by `DERIVATION_TYPE_RULES`, so that values that can never match return 422 ([prod-platform-architecture#233](https://github.com/openbraininstitute/prod-platform-architecture/issues/233)).
- entitycore: filter the expanded derivations by authorization ([prod-platform-architecture#229](https://github.com/openbraininstitute/prod-platform-architecture/issues/229)).
- entitysdk: support `expand` values, including dot paths, in the read and search methods.
- Frontend: handle absent derivation fields like `null`.
- Clients building long `id__in` lists (entitysdk, obi-one): split them into chunks.
- Body-based read endpoint, if query strings become a limit.
