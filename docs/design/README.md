# Design records

Short documents recording design decisions that are not obvious from the code: new entities or activities, changes to relationships, authorization, storage, or API conventions. Small changes that follow the standard patterns (see "Adding a New Entity" in `AGENTS.md`) don't need one.

## Process

1. Copy `TEMPLATE.md` to `YYYY-MM-<short-slug>.md` (e.g. `2026-10-research-log-entity.md`) and set the status to `Draft`.
2. Open a pull request with the record only, for discussion; link it from the related issues.
3. When agreed, set the status to `Accepted`. Either add the implementation to the same PR (small changes) or merge the record and implement in follow-up PRs.
4. Set the status to `Implemented` with the PR links when done. Later changes of direction get a new record; the old one is marked `Superseded by <file>` and otherwise left as is.

Records explain why a change was made. What exists is documented by the code (model docstrings), `docs/asset-labels.md` (generated), and the other files in `docs/`. Implementation steps belong in the pull request description.

entitycore is a public repository: keep records self-contained and don't link internal documents.

## Index

| Record | Status |
|---|---|
| [ResearchLog entity](2026-10-research-log-entity.md) | Accepted |
