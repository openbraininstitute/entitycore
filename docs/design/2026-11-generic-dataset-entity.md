# GenericDataset entity

- Status: Implemented
- Date: 2026-11-20
- Author: @GianlucaFicarelli
- Issues: [#534](https://github.com/openbraininstitute/entitycore/issues/534)
- Pull requests: [#773](https://github.com/openbraininstitute/entitycore/pull/773)

## Context

Users need to upload data that doesn't fit any existing entity type, for two purposes:

- sharing data within a project, e.g. between notebooks, with naming conventions chosen by the project;
- keeping the original files of an entity converted to a supported format, for provenance. Examples are a raw extracellular recording in a vendor format, or the files of a circuit before the conversion to SONATA.

The dataset isn't meant as input of workflows, except for testing and development. Typed workflow results are a separate concern, already covered by `TaskResult` and `TaskConfig`.

## Decision

### Entity

`GenericDataset` is a plain `Entity`, with a name, a description, full-text search, and optional metadata:

```python
class GenericDataset(
    Entity, SubjectMixin, LicensedMixin, NameDescriptionVectorMixin, PrivateOnlyEntityMixin
):
    __tablename__ = EntityType.generic_dataset.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    brain_region_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("brain_region.id"))
    # subject_id and license_id are nullable, from the mixins
```

- The species and strain come from the subject, as for `ScientificArtifact`, so there are no separate `species_id` and `strain_id` columns that could disagree with the subject.
- A dataset cannot reference a private subject in another project, enforced by the same trigger used for `ScientificArtifact.subject_id`.
- There is no `data_category` field: the platform shows all the datasets under "Other". A category can be added later if needed.
- Standard entity routes at `/generic-dataset`, with filters and facets on brain region, subject species and strain, contributions and users.

The joins on the brain region use an outer join when the foreign key is nullable, so the datasets without a brain region are kept when sorting, and are excluded only when filtering on the brain region. Entities with a mandatory brain region keep the inner join.

### Visibility

A generic dataset is always private, because the platform is built around standardized data, and untyped data shouldn't be published. The model inherits the marker `PrivateOnlyEntityMixin`, used to build `PRIVATE_ONLY_ENTITY_TYPES` in `app/db/utils.py`, and the visibility is enforced at three levels:

- API: `GenericDatasetCreate` inherits `PrivateEntityCreate`, where `authorized_public` is `Literal[False]`, so `authorized_public=true` is rejected with 422. The field is excluded from both the user and admin update schemas.
- Database: the check constraint `ck_entity_private_only_types` on the `entity` table rejects public rows of these types, regardless of how they are written.
- Publish: making a project public skips these types, so the datasets and their assets stay private, while the rest of the project is published.

Adding the mixin to another model requires a migration of the check constraint, written manually because Alembic autogenerate doesn't detect check constraints, and the constraint isn't declared in the model because `Entity` is defined before its subclasses. A test compares the constraint in the database with `PRIVATE_ONLY_ENTITY_TYPES`, to detect a missing migration. The type is compared as text, because the migrations run in a single transaction, and a new enum value can't be used in the transaction that adds it.

### Assets

| Label | Kind | Content type | Purpose |
|---|---|---|---|
| `generic_dataset_files` | directory | any | The files of the dataset |
| `generic_dataset_readme` | file | `text/markdown` or `text/plain` | Optional description of the dataset, its format and links to external documentation |

A directory is used instead of a zip archive, because the files of a directory can be listed and downloaded individually. Metadata about the files, if needed, can be stored as a json file inside the directory, as for the `circuit_connectivity_matrices` asset of `Circuit`. There is no limit on the total size beyond the existing limit per file.

## Alternatives considered

- **Child of `ScientificArtifact`.** It would make the subject and the brain region mandatory, while many datasets (e.g. data shared between notebooks) have neither.
- **Public datasets, as for the other entities.** Rejected to avoid publishing untyped data.
- **Enforcing the visibility only in Python.** The publish endpoint updates the rows in bulk without ORM events, and scripts can write directly to the database, so only a database constraint covers every path. A trigger isn't needed, because `type` and `authorized_public` are both columns of `entity`.
- **Optional `species_id` and `strain_id` on the dataset, in addition to the subject.** Redundant with the subject, and the two could disagree.
- **`documentation_url` and `documentation_path` properties.** A readme asset covers both: it can contain the links to the external documentation and describe the content of the directory.
- **A single zip archive.** It can only be downloaded as a whole.

## Consequences

- New table `generic_dataset`, a new `entitytype` value, and two new `assetlabel` values.
- New check constraint `ck_entity_private_only_types` on the `entity` table.
- A dataset can only be used in its own project: derivations and activities in other projects can only use public entities.
- When a project is published, the derivations from a dataset to the converted entities remain visible only to the members of the project.
- A public activity that used a dataset lists it in `used`, because the nested entities of the activities aren't filtered by visibility. This applies to any private entity used by a public activity, and it will be fixed separately.

## Follow-ups

- entitysdk: `GenericDataset` model.
- Platform UI: upload of a directory as a generic dataset, and listing under "Other".
- entitycore: a `DerivationType` linking a generic dataset (used) to the entity converted from it (generated), or an activity for the conversion, once the conversion workflows need it.
- entitycore: filter the `used` and `generated` entities of the activities by visibility.
