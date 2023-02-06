from __future__ import annotations
from dataclasses import dataclass, make_dataclass
import numpy as np
from corsikaio import CorsikaParticleFile
from collections import defaultdict
from particle import Corsika7ID, Particle, InvalidParticle, PDGID
import pandas as pd
from pathlib import Path
from tqdm import tqdm

D0_LIFETIME = Particle.from_name("D0").lifetime
DEFAULT_RUN_HEADER_FEATURES = (
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
)
DEFAULT_EVENT_HEADER_FEATURES = (
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
)


def read_DAT(
    files: Path | [Path] | None = None,
    glob: str | None = None,
    max_events: int | None = None,
    run_header_features: tuple | None = None,
    event_header_features: tuple | None = None,
    additional_columns: bool = True,
    mother_columns: bool = False,
    drop_mothers: bool = True,
    drop_non_particles: bool = True,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Read CORSIKA DAT files to Pandas.DataFrame.
    Exactly one of `files` or `glob` must be provided.
    Made for CORSIKA>7.4, other compatibility not garantueed, but probably approximate.
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

    if files is None and glob is None:
        raise TypeError("`file` and `glob` can't both be None")
    if files is not None and glob is not None:
        raise TypeError("`file` and `glob` can't both be not None")

    if glob is not None:
        basepath = Path(files).parent
        files = list(basepath.glob(Path(files).name))

    if run_header_features is None:
        run_header_features = DEFAULT_RUN_HEADER_FEATURES

    if event_header_features is None:
        event_header_features = DEFAULT_EVENT_HEADER_FEATURES

    if not isinstance(files, list):
        files = [files]

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

    # Check how many showers are there
    n_events = 0
    if max_events is None:
        for file in files:
            with CorsikaParticleFile(file) as f:
                n_events += f.run_header["n_showers"]
    else:
        n_events = max_events

    with tqdm(total=n_events) as pbar:
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

            # this follows the MCEq definition
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
