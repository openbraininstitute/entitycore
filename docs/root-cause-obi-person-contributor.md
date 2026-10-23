# Root-cause analysis: "OBI" recorded as a person contributor

## Summary

In the contributor list of some entities, the Open Brain Institute appears
twice in two different forms:

- a **person** agent named `OBI`, and
- an **organization** agent named `Open Brain Institute, Lausanne, Switzerland`.

These are two distinct `agent` rows. The person `OBI` is not a real individual;
it is the agent that was auto-created for the **shared OBI login account**. Some
contributions were attached to that person agent instead of the organization,
which is why the same contributor shows up inconsistently.

This document explains how the data got into that state and lists options to
stop it from recurring. The one-time data cleanup is handled separately by the
Alembic migration `fc5e781407a6`
(`repoint OBI person contributions to Open Brain Institute organization`).

## Evidence (staging)

Verified read-only against the staging `entitycore` database:

| Agent | `agent.id` | `type` | contributions |
| --- | --- | --- | --- |
| `OBI` | `cd613e30-d8f1-4adf-91b7-584a2265b1f5` | `person` | 14 |
| `Open Brain Institute, Lausanne, Switzerland` | `5f799c26-eac4-45eb-b203-d73b93b4bde1` | `organization` | 239 |

Additional findings:

- The `OBI` person has `given_name = NULL`, `family_name = NULL` — consistent
  with an institutional/service account, not a human.
- The `OBI` person has a non-null `person.sub_id` pointing at a
  `platform_user` row whose `pref_label` is also `OBI` (created
  `2025-06-27`). So the person agent is bound to a real Keycloak login.
- All 14 person contributions use the `unspecified` role and sit on 14
  distinct entities.
- None of those 14 entities already has an organization contribution for the
  same role, so repointing them to the organization does not violate
  `unique_contribution_1 (entity_id, role_id, agent_id)`.

The behaviour is identical in production (UUIDs differ); this is why the cleanup
migration resolves the agents by `pref_label` + `type` rather than by hardcoded
UUID.

## Root cause

Two independent facts combine to produce the symptom.

### 1. Every login becomes a `person` agent

`app/queries/utils.py::get_or_create_user_agent()` is called whenever an
authenticated user creates or updates an entity. For any subject that does not
yet have an agent, it unconditionally creates a **`Person`**:

```python
db_agent = Person(
    id=agent_id,
    pref_label=user_profile.name,     # -> "OBI" for the shared account
    given_name=user_profile.given_name,
    family_name=user_profile.family_name,
    sub_id=user_profile.subject,
    created_by_id=agent_id,
    updated_by_id=agent_id,
)
```

There is no special-casing for shared or institutional accounts. The shared
"OBI" account therefore gets a `Person` agent named `OBI`. This agent is correct
and expected as a `created_by` / `updated_by` value — it just should not be used
as a *contributor* standing in for the institution.

### 2. Contributions are assigned by the client, not auto-derived

entitycore does **not** auto-create `Contribution` rows from the creator. Every
`Contribution(...)` reference in the service layer is read-side
(`selectinload` / joins). Contributions are created explicitly through the
contribution API (`app/service/contribution.py::create_one`) with an `agent_id`
chosen by the caller.

So the 14 bad rows were created by a client (the core-web-app contribution /
upload flow, or an upload script) that passed the **current user's person
agent id** — the `OBI` person returned for the shared login — as the
contributor, instead of the **Open Brain Institute organization** agent id.

### Conclusion

The `OBI` person agent exists purely because the shared OBI account logged in.
It became a contributor because a client used "the current user's agent" as the
contributor id for institutional uploads, rather than selecting the
organization agent. Nothing in entitycore forces a person vs. organization
choice at contribution-creation time, so the mistake was accepted and stored.

## Fix 1 — data cleanup (this change)

Alembic migration `fc5e781407a6` repoints the mis-attached contributions from
the `OBI` person to the `Open Brain Institute` organization:

- resolves both agents at runtime by `pref_label` + `type` (environment
  agnostic);
- is a no-op if either agent is absent (fresh/dev databases);
- repoints only rows that will not collide on
  `unique_contribution_1 (entity_id, role_id, agent_id)`;
- deletes any colliding leftovers (an equivalent organization contribution
  already exists, so the person row is a duplicate);
- `downgrade()` is an intentional no-op: once merged, repointed rows are
  indistinguishable from original organization contributions, so a blind
  reverse would corrupt legitimate data.

Dry-run (read-only) on staging matched the analysis exactly: `would_update=14`,
`would_delete=0`.

This corrects the existing data but does **not** prevent recurrence; if the
shared account keeps creating entities with the same client behaviour, new
person-contributions can reappear.

## Fix 2 — preventing recurrence (needs a maintainer decision)

The durable fix is behavioural and has a few possible homes. These are options,
not a chosen implementation:

1. **Client-side (core-web-app / upload scripts)** — when the acting account is
   the institutional OBI account, submit the **organization** agent id as the
   contributor instead of the current user's person agent. Lowest blast radius;
   keeps entitycore generic. Likely the most appropriate layer, since the
   person-vs-organization contributor choice is a product decision the client
   already makes.

2. **entitycore mapping** — maintain a mapping from known institutional subjects
   to their organization agent, and resolve contributions (and/or
   `created_by`) through it. Centralises the rule but adds configuration and
   couples entitycore to specific accounts.

3. **entitycore guardrail** — add validation so an institutional/shared account
   cannot be stored as a `person` contributor, or so a contribution cannot use a
   person agent that is really an institution. Prevents the class of bug but
   needs a reliable signal to distinguish shared accounts from individuals.

Recommendation: treat Fix 1 (this migration) as the immediate correction, and
open a follow-up to decide between options 1–3 for the behavioural fix. Option 1
is the smallest and most likely correct change; options 2 and 3 are worth
considering if the same mistake can be made by multiple clients.
