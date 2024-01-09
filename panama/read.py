"""
Functions concerning input of CORSIKA7 DAT files.
"""

from __future__ import annotations

from math import inf
from pathlib import Path

import numpy as np
import pandas as pd
from corsikaio import CorsikaParticleFile
from corsikaio.subblocks import event_header_types, particle_data_dtype
from particle import Corsika7ID, Particle
from tqdm import tqdm

from .constants import (
    CORSIKA_FIELD_BYTE_LEN,
    DEFAULT_EVENT_HEADER_FEATURES,
    DEFAULT_RUN_HEADER_FEATURES,
    PDGID_ERROR_VAL,
)
from .prompt import is_prompt_lifetime_limit


def read_DAT(
    files: Path | list[Path] | None = None,
    glob: str | None = None,
    max_events: int | None = None,
    run_header_features: list[str] | None = None,
    event_header_features: list[str] | None = None,
    additional_columns: bool = True,
    mother_columns: bool = False,
    drop_mothers: bool = True,
    drop_non_particles: bool = True,
    noparse: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Read CORSIKA DAT files to Pandas.DataFrame.
    Exactly one of `files` or `glob` must be provided.
    Made for CORSIKA>7.4, other compatibility not garantueed, but probably approximate.
    All energies and masses are given in :math:`\mathrm{GeV}`, while lifetimes are given
    in :math:`\mathrm{ns}`.
    All other units follow the CORSIKA7 definitions, look at its userguide.

    Parameters
    ----------
    files: Path or List of Paths
        Single or list of DAT files to read into the dataframe.
        They must all have unique run_numbers and
        event_numbers.
        If None `glob` must be provided
    glob:
        Globbing expression like `path/to/corsika/output/DAT*`.
        If None, `files` must be provided.
    max_events: int | None
        Maximum number of events to read in.
        If None, read in everything.
    run_header_features: tuple or None
        Names of the run header to actually save,
        corresponding to the naming of `pycorsikaio`.
        If None uses a default list.
        (default: None)
    event_header_features: tuple or None
        Names of the event header to actually save,
        corresponding to the naming of `pycorsikaio`.
        If None uses a default list.
        (default: None)
    additional_columns: bool
        Weather to add (and calculate) additional columns
        not present in standard corsika output, to
        make life easier. They take minimal time to
        calculate.
        These include:
            - `corsikaid`
            - `hadron_gen`
            - `n_obs_level`
            - `is_mother`
            - `pdgid`
            - `mass`
            - `energy`
            - `zenith`
    mother_columns: bool
        Weather to add columns related to the mother/grandmother
        output of the EHIST option.
        They take more time to calculate, since the
        rows are dependent of each other.
    drop_mothers: bool
        Weather to remove all mother rows (default: True)
    drop_non_particles: bool
        Weather to remove all rows not representing a real particle (like muon additional information)
        (default: True)
    noparse:
        Use the "noparse" feature of pycorsikaio, which theoretically
        makes reading in the corsika files faster

    Returns
    -------
    A tuple (run_header, event_header, particles):
        run_header: pandas.DataFrame
            DataFrame with the information about each run
        event_header: pandas.DataFrame
            DataFrame with the information about each event
        particles: pandas.DataFrame
            DataFrame with the information about each particle
    """  # noqa: W605

    if files is None and glob is None:
        raise ValueError("`file` and `glob` can't both be None")
    if files is not None and glob is not None:
        raise ValueError("`file` and `glob` can't both be not None")

    if not additional_columns:
        if drop_non_particles:
            raise ValueError(
                "drop_non_particles requires additional_columns to be calculated."
            )
        if mother_columns:
            raise ValueError(
                "mother_columns requires additional_columns to be calculated"
            )

    if glob is not None:
        basepath = Path(glob).parent
        files = list(basepath.glob(Path(glob).name))
    elif isinstance(files, Path):
        files = [files]

    assert isinstance(files, list)

    if run_header_features is None:
        run_header_features = DEFAULT_RUN_HEADER_FEATURES

    if event_header_features is None:
        event_header_features = DEFAULT_EVENT_HEADER_FEATURES

    run_headers = []
    event_headers = []
    particles = []

    # to index the particles
    particles_run_num = []
    particles_event_num = []
    particles_num: list[int] = []

    events = 0

    # Check how many showers are there
    n_events = 0
    if max_events is None:
        for file in files:
            with CorsikaParticleFile(file) as f:
                n_events += f.run_header["n_showers"]
    else:
        n_events = max_events

    version = None

    with tqdm(total=n_events) as pbar:
        for file in files:
            with CorsikaParticleFile(file, parse_blocks=not noparse) as f:
                run_headers.append([f.run_header[key] for key in run_header_features])
                run_idx = int(f.run_header["run_number"])

                version = float(str(f.run_header["version"])[:3])

                for event in f:
                    if noparse:
                        event_headers.append(event.header)
                    else:
                        event_headers.append(
                            [event.header[key] for key in event_header_features]
                        )

                    if noparse:
                        event_idx = int(
                            event.header[
                                event_header_types[version].fields["event_number"][1]
                                // 4
                            ]
                        )
                    else:
                        event_idx = int(event.header["event_number"])

                    pbar.update(n=1)
                    events += 1

                    if max_events is not None and events >= max_events:
                        break

                    # if noparse:
                    #     n_particles = np.sum(event.particles[:, 1] != 0.0)
                    # else:
                    n_particles = event.particles.shape[0]

                    if n_particles == 0:
                        continue

                    particles.append(event.particles)

                    particles_run_num += [run_idx] * n_particles
                    particles_event_num += [event_idx] * n_particles
                    particles_num += range(n_particles)

    df_run_headers = pd.DataFrame(run_headers, columns=run_header_features)
    df_run_headers.set_index(keys=["run_number"], inplace=True)

    if noparse:
        df_event_headers = pd.DataFrame(np.array(event_headers))
        valid_columns = [
            v[1] // CORSIKA_FIELD_BYTE_LEN
            for v in list(event_header_types[version].fields.values())
        ]
        valid_names = event_header_types[version].names

        mapper = dict(zip(valid_columns, valid_names))

        df_event_headers.drop(
            columns=df_event_headers.columns.difference(valid_columns), inplace=True
        )
        df_event_headers.rename(columns=mapper, inplace=True)
        df_event_headers["run_number"] = df_event_headers["run_number"].astype(int)
        df_event_headers["event_number"] = df_event_headers["event_number"].astype(int)
    else:
        df_event_headers = pd.DataFrame(event_headers, columns=event_header_features)
    df_event_headers.set_index(keys=["run_number", "event_number"], inplace=True)

    # finished parsing if no particles reached observation level
    if len(particles) == 0:
        return df_run_headers, df_event_headers, pd.DataFrame([])

    if noparse:
        # necessary since we can have a different number of particles in each event
        df_particles_l = [pd.DataFrame(p) for p in particles]

        df_particles = pd.concat(df_particles_l, ignore_index=True)

        valid_columns = [
            v[1] // CORSIKA_FIELD_BYTE_LEN
            for v in list(particle_data_dtype.fields.values())
        ]
        valid_names = particle_data_dtype.names

        mapper = dict(zip(valid_columns, valid_names))

        df_particles.drop(
            columns=df_particles.columns.difference(valid_columns), inplace=True
        )
        df_particles.rename(columns=mapper, inplace=True)
        df_particles.query("particle_description != 0", inplace=True)
    else:
        # Hopefully this is more of O(events) than O(particles)
        np_particles = np.empty(
            (sum([p.shape[0] for p in particles]),), dtype=particles[0].dtype
        )
        n = 0
        for p in particles:
            n_p = p.shape[0]
            np_particles[n : n + n_p] = p
            n += n_p

        df_particles = pd.DataFrame(np_particles)

    df_particles["run_number"] = pd.Series(particles_run_num, dtype=int)
    df_particles["event_number"] = pd.Series(particles_event_num, dtype=int)
    df_particles["particle_number"] = pd.Series(particles_num, dtype=int)

    if additional_columns:
        df_particles["corsikaid"] = pd.Series(
            np.abs(df_particles["particle_description"]) // 1000, dtype=int
        )
        df_particles["hadron_gen"] = pd.Series(
            (df_particles["particle_description"].abs() % 1000) // 10,
            dtype=int,
        )
        df_particles["n_obs_level"] = pd.Series(
            df_particles["particle_description"].abs() % 10,
            dtype=int,
        )
        df_particles["is_mother"] = df_particles["particle_description"] < 0

        # the use of pd.NA is currently experimental in Int64 type columns
        corsikaids = df_particles["corsikaid"].unique()
        pdg_map = {
            corsikaid: int(Corsika7ID(corsikaid).to_pdgid())
            if Corsika7ID(corsikaid).is_particle()
            else PDGID_ERROR_VAL  # This will be our error value
            for corsikaid in corsikaids
        }
        df_particles["pdgid"] = (
            df_particles["corsikaid"].map(pdg_map).astype(int, copy=False)
        )

        pdgids = df_particles["pdgid"].unique()

        mass_map = {}
        for pdgid in pdgids:
            if pdgid == PDGID_ERROR_VAL:
                mass_map[pdgid] = 0
            else:
                mass = Particle.from_pdgid(pdgid).mass
                mass_map[pdgid] = mass / 1000 if mass is not None else 0  # GeV

        df_particles["mass"] = df_particles["pdgid"].map(mass_map, na_action=None)
        df_particles["energy"] = df_particles.eval("sqrt(mass**2+px**2+py**2+pz**2)")
        df_particles["zenith"] = df_particles.eval("arccos(pz/sqrt(px**2+py**2+pz**2))")

        if mother_columns:
            add_mother_columns(df_particles, pdgids)

    if drop_mothers:
        df_particles.drop(
            index=df_particles.query("particle_description < 0").index,
            inplace=True,
        )

    if drop_non_particles:
        df_particles.drop(index=df_particles.query("pdgid == 0").index, inplace=True)

    df_particles.set_index(
        keys=["run_number", "event_number", "particle_number"], inplace=True
    )

    return df_run_headers, df_event_headers, df_particles


def add_mother_columns(
    df_particles: pd.DataFrame, pdgids: list[int] | None = None
) -> None:
    """
    Adds the information from mother and grandmother rows to
    the column of the daughter particle.

    This looks so complicated, since in the table different rows
    depend on each other. To do this in a numpy-friendly way is not
    that trivial. (We do not want to iterate through the rows -> python loops)
    So this is done via a shifted index array.

    Parameters
    ----------
    df_particles : DataFrame
        the particle dataframe with additional columns from read_DAT
    pdgids : list[int] | None
        The unique pdgids in the dataframe. If none, they are calculated.
    """
    if pdgids is None:
        pdgids = df_particles["pdgid"].unique()

    mother_index = np.arange(-2, df_particles.shape[0] - 2)
    mother_index[0] = df_particles.shape[0] - 2
    mother_index[1] = df_particles.shape[0] - 1

    grandmother_index = np.arange(-1, df_particles.shape[0] - 1)
    grandmother_index[0] = df_particles.shape[0] - 1

    df_particles["has_mother"] = df_particles["is_mother"].iloc[mother_index].to_numpy(
        copy=False
    ) & df_particles["is_mother"].iloc[grandmother_index].to_numpy(copy=False)

    df_particles["mother_hadr_gen"] = (
        np.abs(df_particles["particle_description"].iloc[mother_index]) % 100
    )
    df_particles.loc[~df_particles["has_mother"], "mother_hadr_gen"] = pd.NA

    # copy mother values to daughter columns so we can drop them later
    for name, error_val in (
        ("pdgid", PDGID_ERROR_VAL),
        ("energy", pd.NA),
        ("mass", pd.NA),
    ):
        df_particles[f"mother_{name}"] = (
            df_particles[name].iloc[mother_index].to_numpy(copy=False)
        )
        df_particles.loc[~df_particles["has_mother"], f"mother_{name}"] = error_val

    # copy grandmother values to daughter columns so we can drop them later
    for name, error_val in (("pdgid", PDGID_ERROR_VAL),):
        df_particles[f"grandmother_{name}"] = (
            df_particles[name].iloc[grandmother_index].to_numpy(copy=False)
        )
        df_particles.loc[~df_particles["has_mother"], f"mother_{name}"] = error_val

    has_charm = {
        pdgid: "c" in Particle.from_pdgid(pdgid).quarks.lower()
        if pdgid != PDGID_ERROR_VAL
        else False
        for pdgid in pdgids
    }

    # this follows the MCEq definition
    lifetimes = {
        pdgid: Particle.from_pdgid(pdgid).lifetime if pdgid != PDGID_ERROR_VAL else inf
        for pdgid in pdgids
    }
    for pdgid in lifetimes:
        if lifetimes[pdgid] is None:
            lifetimes[pdgid] = 0

    is_resonance = {
        pdgid: "*" in Particle.from_pdgid(pdgid).name
        if pdgid != PDGID_ERROR_VAL
        else False
        for pdgid in pdgids
    }

    df_particles["mother_lifetimes"] = df_particles["mother_pdgid"].map(
        lifetimes, na_action=None
    )
    df_particles["mother_is_resonance"] = df_particles["mother_pdgid"].map(
        is_resonance, na_action=None
    )

    dif = df_particles["hadron_gen"].to_numpy(copy=False) - df_particles[
        "mother_hadr_gen"
    ].to_numpy(copy=False)

    df_particles["mother_has_charm"] = df_particles["mother_pdgid"].map(
        has_charm, na_action=None
    )

    is_pion_decay = (dif == 51) & (
        (df_particles["mother_pdgid"].to_numpy(copy=False) == 111)
        | (df_particles["mother_pdgid"].to_numpy(copy=False) == 211)
        | (df_particles["mother_pdgid"].to_numpy(copy=False) == -211)
    )

    is_charm_decay = df_particles["mother_has_charm"].to_numpy(copy=False) & (dif == 30)

    # this adds a cleaned version of the mother_pdgid
    # where the pdgid is replaced with the pdg error value
    # if we can't tell the motherpdgid for sure
    df_particles["mother_pdgid_cleaned"] = df_particles["mother_pdgid"]
    no_true_mother_idxs = ~(
        (
            ((dif == 1) | (dif == 0))
            & ~df_particles["mother_is_resonance"].to_numpy(copy=False)
        )
        | is_charm_decay
        | is_pion_decay
    )
    df_particles.loc[
        no_true_mother_idxs,
        "mother_pdgid_cleaned",
    ] = PDGID_ERROR_VAL

    df_particles["is_prompt"] = is_prompt_lifetime_limit(df_particles)
