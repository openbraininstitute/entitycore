# ExtracellularRecording entity

- Status: Draft
- Date: 2026-11-03
- Author: @james-isbister
- Issues:
- Pull requests: [#752](https://github.com/openbraininstitute/entitycore/pull/752)

## Context

The spike sorting pipeline in obi-one takes a raw extracellular probe recording (e.g. Neuropixels) as an NWB file. The only entity that can hold one today is `ElectricalCellRecording` with `recording_type` `extracellular`. That type describes a single-cell recording: it carries e-types, a liquid junction potential and a hoc-style `recording_location`, and the platform lists it with the cell electrophysiology data.

This is a first, minimal version for prototyping the pipeline. Probe metadata (probe names and types, channel counts) and links to the simulations that simulated recordings come from are deferred.

## Decision

### Entity

`ExtracellularRecording` is a child of `ScientificArtifact`, so it has a subject, brain region and license, with a name, a description and full-text search:

```python
class ExtracellularRecording(ScientificArtifact, NameDescriptionVectorMixin):
    __tablename__ = EntityType.extracellular_recording.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scientific_artifact.id"), primary_key=True)
    sampling_frequency: Mapped[float]  # raw traces, Hz
    duration: Mapped[float]            # seconds
```

The probe geometry stays in the NWB electrodes table, where the analysis tools read it. Standard entity routes at `/extracellular-recording`, with range filters on `sampling_frequency` and `duration`.

### Assets

| Label | Kind | Content type | Purpose |
|---|---|---|---|
| `nwb` | file | `application/nwb` | Voltage traces and the electrodes table |

## Alternatives considered

- **`ElectricalCellRecording` with `recording_type` `extracellular`.** Works without changes, but mixes probe recordings into the single-cell data.
- **A child of `ElectricalRecording`, beside `ElectricalCellRecording` and `IonChannelRecording`.** It would inherit `recording_location`, `ljp` and the stimuli, which describe single-cell recordings and don't apply here.

## Consequences

- New table `extracellular_recording` and a new `entitytype` value. No change to existing tables.

## Follow-ups

- entitysdk: `ExtracellularRecording` model.
- obi-one: take an `ExtracellularRecording` as input to the spike sorting pipeline.
- entitycore: probe metadata, and links from simulated recordings to their simulation results, once the pipeline needs them.
