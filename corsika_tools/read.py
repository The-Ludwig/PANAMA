from __future__ import annotations
from dataclasses import dataclass, make_dataclass
import numpy as np
from corsikaio import CorsikaParticleFile
from collections import defaultdict
from particle import Corsika7ID, Particle, InvalidParticle, PDGID
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from .fluxes import FastHillasGaisser2012

D0_LIFETIME = Particle.from_name("D0").lifetime


def _mother_idx(is_mother: np.ndarray, index: np.ndarray) -> np.ndarray:
    mi = np.empty(index.shape, dtype=index.dtype)
    mi[0] = None
    mi[1] = None
    for i in range(2, len(is_mother)):
        mi[i] = index[i - 2] if is_mother[i - 1] and is_mother[i - 2] else None
    return mi


# @njit
def _mother_idx_numba(
    is_mother: np.ndarray,
    run_idx: np.ndarray,
    event_idx: np.ndarray,
    particle_idx: np.ndarray,
) -> tuple[np.ndarray]:
    """
    Numba-compatible version of mother_idx, performance boost is approx x6 (6secs->1secs),
    But UI is worse since the index can't be None (no object...), so I am just gonna eat the 6 seconds
    """
    mi_run = np.empty(run_idx.shape, dtype=run_idx.dtype)
    mi_event = np.empty(event_idx.shape, dtype=event_idx.dtype)
    mi_parti = np.empty(particle_idx.shape, dtype=particle_idx.dtype)

    mi_run[0] = -1
    mi_run[1] = -1
    mi_event[0] = -1
    mi_event[1] = -1
    mi_parti[0] = -1
    mi_parti[1] = -1

    for i in range(2, len(is_mother)):
        mi_run[i] = run_idx[i - 2] if is_mother[i - 1] and is_mother[i - 2] else -1
        mi_event[i] = event_idx[i - 2] if is_mother[i - 1] and is_mother[i - 2] else -1
        mi_parti[i] = (
            particle_idx[i - 2] if is_mother[i - 1] and is_mother[i - 2] else -1
        )

    return (mi_run, mi_event, mi_parti)


# @njit
def _mother_idx_numba_ez(
    is_mother: np.ndarray, index: np.ndarray, none_val: np.ndarray
) -> np.ndarray:
    """
    Numba-compatible version of mother_idx, performance boost is approx x6 (6secs->1secs),
    But UI is worse since the index can't be None (no object...), so I am just gonna eat the 6 seconds
    """
    mi = np.empty(index.shape, dtype=index.dtype)

    mi[0] = none_val
    mi[0] = none_val

    for i in range(2, len(is_mother)):
        mi[i] = index[i - 2] if is_mother[i - 1] and is_mother[i - 2] else none_val
    return mi


def add_weight(df_run, df_event, df, model=FastHillasGaisser2012(model="H3a")):
    """
    Adds the collumn "weight" too df_particle to reweight for given primary flux.

    Parameters
    ----------
    df_run: The run dataframe (as returned by `read_corsika_particle_files_to_dataframe`)
    df_event: The event dataframe (as returned by `read_corsika_particle_files_to_dataframe`)
    df: The particle dataframe (as returned by `read_corsika_particle_files_to_dataframe`)
    model: The Cosmic Ray primary flux model (instance of CRFlux)
    """
    primary_pids = df_event["particle_id"].unique()
    energy_slopes = df_run["energy_spectrum_slope"].unique()
    emaxs = df_run["energy_max"].unique()
    emins = df_run["energy_min"].unique()

    assert len(primary_pids) == 1
    assert len(energy_slopes) == 1
    assert len(emaxs) == 1
    assert len(emins) == 1

    primary_pid, energy_slope = primary_pids[0], energy_slopes[0]
    emin, emax = emins[0], emaxs[0]

    N = 1
    if energy_slope == -1:
        N = np.log(emax / emin)
    else:
        ep = energy_slope + 1
        N = (emax**ep - emin**ep) / ep

    flux = lambda E: sum(model.p_and_n_flux(E)[1:])

    ext_pdf = df_event.shape[0] * (df_event["total_energy"] ** energy_slope) / N

    df["weight"] = flux(df_event["total_energy"]) / ext_pdf


def add_weight_prompt(df, prompt_factor):
    """
    Adds collumn "weight_prompt" to df, to set a weight for every prompt particle, non prompt particles get weight 1
    """
    df["weight_prompt"] = 1.0
    df.loc[df["is_prompt"] == True, "weight_prompt"] = prompt_factor


def add_weight_prompt_per_event(df, prompt_factor):
    """
    Adds collumn "weight_prompt_per_event" to df, which will be `prompt_factor` for every particle, which is inside
    a shower, which has at least one prompt muon. For every other particle, it will be 1.
    """
    # For some weird reason this makes a difference, as the last line of this function does not work otherwise
    if not df.index.is_monotonic_increasing:
        df.sort_index(inplace=True)

    df["weight_prompt_per_event"] = 1.0

    indexes = df.query("is_prompt == True").index
    evt_idxs = {i[0]: set() for i in indexes}
    for i in indexes:
        evt_idxs[i[0]].add(i[1])

    for i in evt_idxs:
        df.loc[i].loc[list(evt_idxs[i]), "weight_prompt_per_event"] = prompt_factor


def read_corsika_particle_glob_to_dataframe(
    files: str, **kwargs
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calls `read_corsika_particle_files_to_dataframe` for every globbed file.
    """
    basepath = Path(files).parent
    files = list(basepath.glob(Path(files).name))
    return read_corsika_particle_files_to_dataframe(files, **kwargs)


def read_corsika_particle_files_to_dataframe(
    files: [Path],
    max_events: int | None = None,
    run_header_features: tuple = (
        "run_number",
        "date",
        "version",
        "n_observation_levels",
        "observation_height",
        "energy_spectrum_slope",
        "energy_min",
        "energy_max",
        "energy_cutoff_hadrons",
        "energy_cutoff_muons",
        "energy_cutoff_electrons",
        "energy_cutoff_photons",
        "n_showers",
    ),
    event_header_features: tuple = (
        "event_number",
        "run_number",
        "particle_id",
        "total_energy",
        "starting_altitude",
        "first_interaction_height",
        "momentum_x",
        "momentum_y",
        "momentum_minus_z",
        "zenith",
        "azimuth",
        "low_energy_hadron_model",
        "high_energy_hadron_model",
        "sybill_interaction_flag",
        "sybill_cross_section_flag",
        "explicit_charm_generation_flag",
    ),
    additional_columns: bool = True,
    mother_columns: bool = False,
    drop_mothers: bool = True,
    drop_non_particles: bool = True,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Parameters
    ----------
    files: List of Paths
        List of Paths to read into the dataframe.
        They must all have unique run_numbers and
        event_numbers.
    max_events: int | None
        Maximum number of events to read in.
        If None, read in everything.
    run_header_features: tuple
        Names of the run header to actually save,
        corresponding to the naming of `pycorsikaio`.
    event_header_features: tuple
        Names of the event header to actually save,
        corresponding to the naming of `pycorsikaio`.
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
        columns are dependend of each other.
    drop_mothers: bool
        Weather to remove all mother rows (default: True)
    drop_non_particles: bool
        Weather to remove all rows not representing a real particle (like muon additional information)
        (default: True)

    Returns
    -------
    A tuple (run_header, event_header, particles) with:
    run_header: pandas.DataFrame
        DataFrame with the information about each run
    event_header: pandas.DataFrame
        DataFrame with the information about each event
    particles: pandas.DataFrame
        DataFrame with the information about each particle
    """

    run_headers = []
    event_headers = []
    particles = []

    # to index the particles
    particles_run_num = []
    particles_event_num = []
    particles_num = []

    events = 0

    # flag to break
    finished = False

    with tqdm(total=max_events) as pbar:
        for file in files:

            if finished:
                break

            with CorsikaParticleFile(file) as f:

                run_headers.append([f.run_header[key] for key in run_header_features])
                run_idx = int(f.run_header["run_number"])

                for event in f:
                    event_headers.append(
                        [event.header[key] for key in event_header_features]
                    )
                    event_idx = int(event.header["event_number"])

                    pbar.update(n=1)
                    events += 1

                    if max_events is not None and events > max_events:
                        finished = True
                        break

                    n_particles = event.particles.shape[0]

                    if n_particles == 0:
                        continue

                    particles.append(event.particles)

                    particles_run_num += [run_idx] * n_particles
                    particles_event_num += [event_idx] * n_particles
                    particles_num += range(n_particles)

    df_run_headers = pd.DataFrame(run_headers, columns=run_header_features)
    df_run_headers.set_index(keys=["run_number"], inplace=True)

    df_event_headers = pd.DataFrame(event_headers, columns=event_header_features)
    df_event_headers.set_index(keys=["run_number", "event_number"], inplace=True)

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

        pdg_error_val = (
            0  # This non-existing pdgid will be our error value for now, since
        )
        # the use of pd.NA is currently experimental in Int64 type columns
        corsikaids = df_particles["corsikaid"].unique()
        pdg_map = {
            corsikaid: int(Corsika7ID(corsikaid).to_pdgid())
            if Corsika7ID(corsikaid).is_particle()
            else pdg_error_val  # This will be our error value
            for corsikaid in corsikaids
        }
        df_particles["pdgid"] = (
            df_particles["corsikaid"].map(pdg_map).astype(int, copy=False)
        )

        pdgids = df_particles["pdgid"].unique()
        mass_map = {
            pdgid: Particle.from_pdgid(pdgid).mass / 1000  # GeV
            if pdgid != pdg_error_val
            else 0
            for pdgid in pdgids
        }
        df_particles["mass"] = df_particles["pdgid"].map(mass_map, na_action=None)
        df_particles["energy"] = df_particles.eval("sqrt(mass**2+px**2+py**2+pz**2)")
        df_particles["zenith"] = df_particles.eval("arccos(pz/sqrt(px**2+py**2+pz**2))")

        if mother_columns:
            mother_index = np.arange(-2, df_particles.shape[0] - 2)
            mother_index[0] = df_particles.shape[0] - 2
            mother_index[1] = df_particles.shape[0] - 1

            grandmother_index = np.arange(-1, df_particles.shape[0] - 1)
            grandmother_index[0] = df_particles.shape[0] - 1

            df_particles["has_mother"] = (
                df_particles["is_mother"].iloc[mother_index].values
                & df_particles["is_mother"].iloc[grandmother_index].values
            )

            df_particles["mother_pdgid"] = (
                df_particles["pdgid"].iloc[mother_index].values
            )
            df_particles.loc[
                ~df_particles["has_mother"].values, "mother_pdgid"
            ] = pdg_error_val

            df_particles["mother_corsikaid"] = (
                df_particles["corsikaid"].iloc[mother_index].values
            )
            df_particles.loc[
                ~df_particles["has_mother"].values, "mother_corsikaid"
            ] = pdg_error_val

            df_particles["mother_hadr_gen"] = (
                np.abs(df_particles["particle_description"].iloc[mother_index].values)
                % 100
            )
            df_particles.loc[
                ~df_particles["has_mother"].values, "mother_hadr_gen"
            ] = pd.NA

            has_charm = {
                pdgid: "c" in Particle.from_pdgid(pdgid).quarks.lower()
                if pdgid != pdg_error_val
                else pd.NA
                for pdgid in pdgids
            }

            lifetime_limit = Particle.from_name("D0").lifetime * 10
            lifetimes = {
                pdgid: Particle.from_pdgid(pdgid).lifetime
                if pdgid != pdg_error_val
                else lifetime_limit + 10
                for pdgid in pdgids
            }
            for pdgid in lifetimes:
                if lifetimes[pdgid] is None:
                    lifetimes[pdgid] = 0

            mother_has_charm = df_particles["mother_pdgid"].map(
                has_charm, na_action=None
            )
            mother_lifetimes = df_particles["mother_pdgid"].map(
                lifetimes, na_action=None
            )

            mother_is_resonance = (df_particles["mother_corsikaid"].values <= 65) & (
                df_particles["mother_corsikaid"].values >= 62
            )

            df_particles["mother_has_charm"] = mother_has_charm.values

            dif = (
                df_particles["hadron_gen"].values
                - df_particles["mother_hadr_gen"].values
            )
            df_particles["is_prompt"] = df_particles["has_mother"].values & (
                (
                    (mother_lifetimes.values <= lifetime_limit)
                    & (
                        (np.abs(dif) <= 1 & ~mother_is_resonance)
                        # np.abs because of some very weird stuff going on in ehist
                        | ((dif == 30) & mother_has_charm.values)
                    )
                )
                | (
                    (df_particles["mother_pdgid"].abs().values == 13)
                    & (df_particles["hadron_gen"] < 3)
                )  # mother is muon (and in early generation)
            )

        if drop_mothers:
            df_particles.drop(
                index=df_particles.query("is_mother == True").index.values, inplace=True
            )

        # Numba version...
        # df["mother_run_idx"], df["mother_event_idx"], df["mother_particle_idx"] = mother_idx_numba(df.loc[:, "is_mother"].values, df.loc[:, "run_number"].values, df.loc[:, "event_number"].values, df.loc[:, "particle_number"].values)

    if drop_non_particles:
        df_particles.drop(
            index=df_particles.query("pdgid == 0").index.values, inplace=True
        )

    df_particles.set_index(
        keys=["run_number", "event_number", "particle_number"], inplace=True
    )

    # if additional_columns:
    #    df["mother_idx"] = mother_idx(df["is_mother"].values, df.index.values)

    return df_run_headers, df_event_headers, df_particles
