# ExtracellularRecording entity

- Status: Draft
- Date: 2026-11-03
- Author: @james-isbister
- Issues:
- Pull requests:

## Context

The spike sorting pipeline in obi-one takes a raw extracellular probe recording (e.g. Neuropixels) as an NWB file. The only entity that can hold one today is `ElectricalCellRecording` with `recording_type` `extracellular`. That type describes a single-cell recording: it carries e-types, a liquid junction potential and a hoc-style `recording_location`, and the platform lists it with the cell electrophysiology data. Probe recordings stored there would be shown as cell recordings.

In scope: an entity for extracellular probe recordings, measured or simulated, with its NWB file, and a link from a simulated recording to the simulation result it was computed from. Deferred: sensory stimuli and behaviour during the recording, and the spike sorting outputs (stored as `TaskResult`s of the AIND ephys task types).

## Decision

### Entity

`ExtracellularRecording` is a third child of `ElectricalRecording`, beside `ElectricalCellRecording` and `IonChannelRecording`. It inherits subject, brain region, license, `recording_type`, `recording_origin`, `temperature` and `comment`, and adds the fields that describe a probe recording:

```python
class ExtracellularRecording(ElectricalRecording):
    __tablename__ = EntityType.extracellular_recording.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("electrical_recording.id"), primary_key=True)
    probe_names: Mapped[STRING_LIST]   # as in the NWB file
    channel_count: Mapped[int]         # over all probes
    sampling_frequency: Mapped[float]  # raw traces, Hz
    duration: Mapped[float]            # seconds
```

- `recording_type` defaults to `extracellular`; `recording_origin` is `in_silico` for simulated recordings.
- The inherited `recording_location` and `ljp` are not exposed in the API and keep their defaults (`[]`, `0.0`). `recording_location` gets a Python-side default of `[]` on `ElectricalRecording`, which needs no migration.
- The probe geometry (electrode positions, shanks, groups) stays in the NWB electrodes table, where the analysis tools read it.
- Standard entity routes at `/extracellular-recording`, with filters on recording type and origin, and ranges on `channel_count`, `sampling_frequency` and `duration`.

### Assets

| Label | Kind | Content type | Purpose |
|---|---|---|---|
| `nwb` | file | `application/nwb` | Voltage traces, electrodes table and probes |

### Links to other entities

A recording computed from a simulation is linked to its `SimulationResult` with a `Derivation` of the new type `simulation_result_extracellular_recording` (used: `simulation_result`, generated: `extracellular_recording`), validated by `DERIVATION_TYPE_RULES`. It is read with `GET /extracellular-recording/{id}?expand=generated_from_derivations:simulation_result_extracellular_recording`, and searched with `GET /extracellular-recording?generated_derivation__used_id=<simulation result id>`.

## Alternatives considered

- **`ElectricalCellRecording` with `recording_type` `extracellular`.** Works without changes, but mixes probe recordings into the single-cell data, and exposes fields that don't apply to them.
- **A generic dataset entity with an NWB asset.** Loses the subject, brain region and recording metadata that `ElectricalRecording` already provides.
- **Foreign keys to the simulation result and recording array.** Derivations are the standard for provenance links, typed and validated per derivation type, and need no extra columns for measured recordings.

## Consequences

- New table `extracellular_recording`, new values in `entitytype` and `derivationtype`. No change to existing rows.
- `ElectricalRecordingStimulus` can still reference any electrical recording, but stimuli are not loaded or returned for extracellular recordings.

## Follow-ups

- entitysdk: `ExtracellularRecording` model.
- obi-one: take an `ExtracellularRecording` as input to the spike sorting pipeline, and register simulated recordings with the derivation above.
- Platform: list extracellular recordings separately from cell recordings.

## Open questions

- Should the probe type be a field (e.g. the existing `ElectrodeType` of `SimulatableExtracellularRecordingArray`), given that one recording can combine probes of different types?
- Should a simulated recording also link to the `SimulatableExtracellularRecordingArray` it was computed with, when a simulation has several arrays?
