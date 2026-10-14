# ResearchLog entity

- Status: Draft
- Date: 2026-10-14
- Author: @GianlucaFicarelli
- Issues: [prod-ai#131](https://github.com/openbraininstitute/prod-ai/issues/131), [entitycore#534](https://github.com/openbraininstitute/entitycore/issues/534)
- Pull requests: —

## Context

Agents running in the MCP sandbox produce a markdown logbook describing a research session. Today it lives only in the user's sandbox home directory, so it is visible to its creator alone. Storing it as an entity makes it shareable with the other members of the project, through the standard `authorized_project_id` / `authorized_public` rules, and lets the platform list it under `Reports`.

Only the research log is addressed now. Figures and data tables produced in the same sessions are deferred (see Alternatives considered).

## Decision

### Entity

`ResearchLog` is a direct child of `Entity`, modelled on `AnalysisNotebookResult`: a named, described, project-scoped document whose content lives in its assets, with standard CRUD and no foreign keys.

```python
class ResearchLog(Entity, NameDescriptionVectorMixin):
    """Markdown logbook of a research session, e.g. produced by an agent in the MCP sandbox.

    Attributes:
        id (uuid.UUID): Primary key, referencing the entity ID.
        category (str | None): Free-text category used to group logs.

    Assets:
        - a markdown file with label `research_log`.
        - an optional directory with label `research_log_files`.
    """

    __tablename__ = EntityType.research_log.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    category: Mapped[str | None] = mapped_column(index=True)
    __mapper_args__ = {"polymorphic_identity": __tablename__}
```

`category` is an optional free-text string to group logs (e.g. by topic or workflow), available as a filter. The API is otherwise the standard one for entities, including the generic asset endpoints.

### Assets

| Label | Kind | Content type | Purpose |
|---|---|---|---|
| `research_log` | file | `text/markdown` (new `ContentType.markdown`, suffixes `.md`, `.markdown`) | The logbook |
| `research_log_files` | directory | — | Files embedded or referenced by the logbook (figures, small data files) |

Links in the markdown are relative paths inside the `research_log_files` directory (e.g. `![](figures/fig1.png)`), so the frontend can resolve them through the directory listing and download endpoints.

### Links to other entities

A log is linked to the entities it is about (e.g. the circuit analysed, the simulation results produced in the session) with the existing `Derivation`, using a new `DerivationType.research_log`:

- `generated_id` is the log and `used_id` the referenced entity (PROV `wasDerivedFrom`). The direction is the same also for entities produced during the session, so all links of a log are found from the log side.
- Links are created with `POST /derivation`, which already requires the referenced entity to be readable and the log to be writable.
- `GET /research-log/{id}?expand=generated_from_derivations` returns the referenced entities; `?expand=used_by_derivations` on an entity returns the logs about it.
- A dedicated type, instead of `unspecified`, keeps these links distinguishable from model-building derivations such as `circuit_extraction`.

## Alternatives considered

- **Three entities (ResearchLog, Figure, DataTable).** Proposed in prod-ai#131. Figures and tables need their own metadata (caption, columns) whose shape is still unclear; they may become specialized entities later or reuse the generic dataset entity of entitycore#534. Until then, the files of a log are stored in its `research_log_files` directory.
- **A single generic entity with several assets.** It would group the files, but mixes concepts that the platform displays differently (reports vs. data).
- **Child of `ScientificArtifact`.** A log has no brain region, species, subject, or license.
- **`category` as an enum.** The useful values are not known yet. It can become an enum once conventions emerge.
- **Linking through an activity.** `AnalysisNotebookResult` is linked to the analysed entities through an `AnalysisNotebookExecution` activity (used: analysed entities, generated: result), together with `AnalysisNotebookTemplate` and `AnalysisNotebookEnvironment`. An equivalent "research session" activity would be closer to PROV, but needs a new activity type and only pays off when a session has metadata of its own (agent, model, duration, environment). Existing derivations can be migrated to an activity if that happens.

## Consequences

- Deleting a log removes its links (`generated_id` is `ON DELETE CASCADE`). Deleting a referenced entity is refused while a log links to it (`used_id` has no cascade), as for any derivation today. Since public entities of other projects can be referenced, a log can prevent their owners from deleting them until the link is removed.
- `category` values are not curated: consistency is left to the users and agents writing the logs.
- As for other entities, assets cannot be required at creation: a log may exist without its markdown file until it is uploaded.

## Follow-ups

- entitysdk: `ResearchLog` model and upload helpers.
- Platform: display research logs under `Reports`, rendering the markdown and resolving relative links against `research_log_files`.
- Figures and data tables (entitycore#534).
