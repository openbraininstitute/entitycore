# GenericDataset entity

- Status: Accepted
- Date: 2026-11-20
- Author: @GianlucaFicarelli
- Issues: [#534](https://github.com/openbraininstitute/entitycore/issues/534)
- Pull requests:

## Context

Users need to upload data that doesn't fit any existing entity type, for two purposes:

- sharing data within a project, e.g. between notebooks, with naming conventions chosen by the project;
- keeping the original files of an entity converted to a supported format, for provenance. Examples are a raw extracellular recording in a vendor format, or the files of a circuit before the conversion to SONATA.

The dataset isn't meant as input of workflows, except for testing and development. Typed workflow results are a separate concern, already covered by `TaskResult` and `TaskConfig`.

## Decision

### Entity

`GenericDataset` is a plain `Entity`, with a name, a description, full-text search, and optional metadata:

```python
class GenericDataset(Entity, SubjectMixin, LicensedMixin, NameDescriptionVectorMixin):
    __tablename__ = EntityType.generic_dataset.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    brain_region_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("brain_region.id"))
    # subject_id and license_id are nullable, from the mixins
```

- The species and strain come from the subject, as for `ScientificArtifact`, so there are no separate `species_id` and `strain_id` columns that could disagree with the subject.
- A public dataset cannot reference a private subject, enforced by the same trigger used for `ScientificArtifact.subject_id`.
- There is no `data_category` field: the platform shows all the datasets under "Other". A category can be added later if needed.
- Standard entity routes at `/generic-dataset`, with filters and facets on brain region, subject species and strain, contributions and users.

The joins on the brain region use an outer join when the foreign key is nullable, so the datasets without a brain region are kept when sorting, and are excluded only when filtering on the brain region. Entities with a mandatory brain region keep the inner join.

### Assets

| Label | Kind | Content type | Purpose |
|---|---|---|---|
| `generic_dataset_files` | directory | any | The files of the dataset |
| `generic_dataset_readme` | file | `text/markdown` or `text/plain` | Optional description of the dataset, its format and links to external documentation |

A directory is used instead of a zip archive, because the files of a directory can be listed and downloaded individually. Metadata about the files, if needed, can be stored as a json file inside the directory, as for the `circuit_connectivity_matrices` asset of `Circuit`. There is no limit on the total size beyond the existing limit per file.

## Alternatives considered

- **Child of `ScientificArtifact`.** It would make the subject and the brain region mandatory, while many datasets (e.g. data shared between notebooks) have neither.
- **Optional `species_id` and `strain_id` on the dataset, in addition to the subject.** Redundant with the subject, and the two could disagree.
- **`documentation_url` and `documentation_path` properties.** A readme asset covers both: it can contain the links to the external documentation and describe the content of the directory.
- **A single zip archive.** It can only be downloaded as a whole.

## Consequences

- New table `generic_dataset`, a new `entitytype` value, and two new `assetlabel` values. No change to existing tables.

## Follow-ups

- entitysdk: `GenericDataset` model.
- Platform UI: upload of a directory as a generic dataset, and listing under "Other".
- entitycore: a `DerivationType` linking a generic dataset (used) to the entity converted from it (generated), or an activity for the conversion, once the conversion workflows need it.
