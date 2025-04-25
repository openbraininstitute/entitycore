import hashlib
import shutil

import h5py

from app.cli.mappings import STIMULUS_INFO, ECode

# get old to new ecode mapping. Do not include curated values in keys
ecode_mapping = {
    old_ecode: data["ecode"]
    for old_ecode, data in STIMULUS_INFO.items()
    if old_ecode not in {e.value for e in ECode}
}


def curate(_, source_file, target_file) -> dict:
    """Curate asset file and return new metadata."""
    shutil.copyfile(source_file, target_file)

    _curate_nwb(target_file)

    new_size = target_file.stat().st_size
    with target_file.open(mode="rb") as f:
        new_digest = hashlib.file_digest(f, "sha256").hexdigest()

    return {
        "sha256_digest": new_digest,
        "size": new_size,
        "content_type": "application/nwb",
    }


def _curate_nwb(file_path):
    with h5py.File(file_path, "r+") as f:
        if "data_organization" in f:
            _update_data_organisation(f, ecode_mapping)

        session_descr = f["session_description"][()].decode("UTF-8")  # pyright: ignore [reportIndexIssue]

        if session_descr == "SSCX Simulation Data":
            _sscx_simulation_update(f, "/acquisition/", ecode_mapping)
            _sscx_simulation_update(f, "/stimulus/presentation/", ecode_mapping)
        elif session_descr == "Simulated Thalamus cell":
            _thalamus_simulation_update(f, "/acquisition/", ecode_mapping)
            _thalamus_simulation_update(f, "/stimulus/presentation/", ecode_mapping)
        else:
            _update_path(f, "/acquisition/", ecode_mapping)
            _update_path(f, "/stimulus/presentation/", ecode_mapping)

        _update_stim_type(f, ecode_mapping)


def _thalamus_simulation_update(f, base_path, ecode_mapping):
    """Update a path in /acquisition/ or /stimulus/presentation/.

    Here we rename the protocols according to:
        IV -> IV
        RMP -> SpontaneousNoHold
        Rin_dep -> Rin
        Rin_hyp -> Rin
        Step -> Step
        Step_{number}_hyp -> Step
        hold_dep -> Spontaneous
        hold_hyp -> Spontaneous
    Also, we add ic / ics as a prefix and add a 'unique' index as a suffix
    """
    stim_num = 0
    for old_path in f[base_path]:
        if old_path in ecode_mapping:
            new_ecode = ecode_mapping[old_path]
            new_path = f"{new_ecode}__{stim_num}"
            prefix = _get_prefix(base_path, _get_units(f, base_path, old_path))
            new_path = prefix + new_path

            full_old_path = f"{base_path}{old_path}"
            full_new_path = f"{base_path}{new_path}"

            # update the paths
            if full_old_path not in f:
                continue

            f.move(full_old_path, full_new_path)

        stim_num += 1


def _sscx_simulation_update(f, base_path, ecode_mapping):
    """Update a path in /acquisition/ or /stimulus/presentation/."""
    # should move e.g. step_1 to ic__GenericStep__1 / ics__GenericStep__1
    for old_path in f[base_path]:
        # hard-code edge case here because the '__' in the protocol name messes up the function
        old_ecode = "A___.ibw" if "A___.ibw" in old_path else old_path.split("_")[0]

        if old_ecode in ecode_mapping:
            new_ecode = ecode_mapping[old_ecode]
            new_path = old_path.replace("_", "__").replace(old_ecode, new_ecode)
            prefix = _get_prefix(base_path, _get_units(f, base_path, old_path))
            new_path = prefix + new_path

            full_old_path = f"{base_path}{old_path}"
            full_new_path = f"{base_path}{new_path}"

            # update the paths
            if full_old_path not in f:
                continue

            f.move(full_old_path, full_new_path)


def _update_path(f, base_path, ecode_mapping):
    """Update a path in /acquisition/ or /stimulus/presentation/."""
    for old_path in f[base_path]:
        # hard-code edge case here because the '__' in the protocol name messes up the function
        try:
            old_ecode = "A___.ibw" if "A___.ibw" in old_path else old_path.split("__")[1]
        except IndexError:
            msg = f"Path {old_path} cannot be split."
            raise RuntimeError(msg) from None

        if old_ecode in ecode_mapping:
            full_old_path = f"{base_path}{old_path}"
            full_new_path = base_path + old_path.replace(old_ecode, ecode_mapping[old_ecode])

            if full_old_path not in f:
                continue

            # update the paths
            f.move(full_old_path, full_new_path)


def _update_data_organisation(f, ecode_mapping):
    for cellid in f["/data_organization/"]:
        for old_ecode in f[f"/data_organization/{cellid}"]:
            if old_ecode not in ecode_mapping:
                continue

            new_ecode = ecode_mapping[old_ecode]
            # move stuff with the right ecode folder name.
            # Have to be careful if the folder name is already present.
            _move_data_folder(f, cellid, old_ecode, new_ecode)

            # now that we have the correct protocol folder name, we can rename the data folder
            _rename_data_folder(f, cellid, old_ecode, new_ecode)


def _move_data_folder(f, cellid, old_ecode, new_ecode):
    if f"/data_organization/{cellid}/{new_ecode}" not in f:
        f.move(
            f"/data_organization/{cellid}/{old_ecode}",
            f"/data_organization/{cellid}/{new_ecode}",
        )
    else:
        for rep in f[f"/data_organization/{cellid}/{old_ecode}"]:
            old_rep = f"/data_organization/{cellid}/{old_ecode}/{rep}"
            new_rep = f"/data_organization/{cellid}/{new_ecode}/{rep}"
            if new_rep not in f:
                f.move(old_rep, new_rep)
            else:
                for sweep in f[old_rep]:
                    # sweep number should be unique,
                    # but let's check for it before just to be sure.

                    old_sweep = f"/data_organization/{cellid}/{old_ecode}/{rep}/{sweep}"
                    new_sweep = f"/data_organization/{cellid}/{new_ecode}/{rep}/{sweep}"

                    if new_sweep in f:
                        msg = f"Failed to move {old_sweep} -> {new_sweep}. Already present."
                        raise RuntimeError(msg) from None
                    f.move(old_sweep, new_sweep)
        # now that we have moved subgroups, we still have to 'manually'
        # delete the old empty group that is remaining
        del f[f"/data_organization/{cellid}/{old_ecode}"]


def _rename_data_folder(f, cellid, old_ecode, new_ecode):
    for rep in f[f"/data_organization/{cellid}/{new_ecode}"]:
        for sweep in f[f"/data_organization/{cellid}/{new_ecode}/{rep}"]:
            for old_name in f[f"/data_organization/{cellid}/{new_ecode}/{rep}/{sweep}"]:
                new_name = old_name.replace(old_ecode, new_ecode)
                old_data_organization_path = (
                    f"/data_organization/{cellid}/{new_ecode}/{rep}/{sweep}/{old_name}"
                )
                new_data_organization_path = (
                    f"/data_organization/{cellid}/{new_ecode}/{rep}/{sweep}/{new_name}"
                )

                if old_data_organization_path in f and new_data_organization_path not in f:
                    f.move(old_data_organization_path, new_data_organization_path)


def _update_stim_type(f, ecode_mapping):
    stim_type_path = "general/intracellular_ephys/sequential_recordings/stimulus_type"
    if stim_type_path in f:
        for i in range(len(f[stim_type_path])):
            old_ecode = f[stim_type_path][i].decode("UTF-8")
            if old_ecode in ecode_mapping:
                # It is ok to have multiple times the same protocol name in the list.
                # It is already the case for in multiple nwb files.
                new_ecode = ecode_mapping[old_ecode].encode("UTF-8")
                f[stim_type_path][i] = new_ecode
                f.flush()


def _get_units(f, base_path, old_path):
    units = f[f"{base_path}{old_path}/data"].attrs["unit"]
    return units if isinstance(units, str) else units.decode("UTF-8")


def _get_prefix(base_path, units):
    if "acquisition" in base_path and units == "volts":
        return "ic__"

    if "acquisition" in base_path and units == "amperes":
        return "vc__"

    if "stimulus" in base_path and units == "volts":
        return "vcs__"

    if "stimulus" in base_path and units == "amperes":
        return "ics__"

    msg = f"Failed to calculate prefix for path {base_path} and units {units}"
    raise RuntimeError(msg)
