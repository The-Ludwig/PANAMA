"""
Functions to add weights to the read in corsika dataframe
"""
from typing import Any

import numpy as np
import pandas as pd
from particle import PDGID, Corsika7ID

from .fluxes import CosmicRayFlux, H3a

DEFAULT_FLUX = H3a()


def get_weights(
    df_run: pd.DataFrame,
    df_event: pd.DataFrame,
    df: pd.DataFrame,
    model: CosmicRayFlux = DEFAULT_FLUX,
) -> pd.DataFrame:
    """
    Adds the column "weight" too df_particle to reweight for given primary flux.

    Parameters
    ----------
    df_run: The run dataframe (as returned by `read_corsika_particle_files_to_dataframe`)
    df_event: The event dataframe (as returned by `read_corsika_particle_files_to_dataframe`)
    df: The particle dataframe (as returned by `read_corsika_particle_files_to_dataframe`)
    model: The Cosmic Ray primary flux model (instance of CRFlux)

    Returns
    -------
    weights: A dataframe with the weights labeled by the run and event index.
    Can be used like this: `df['weights'] = panama.get_weights(df_run, df_event, df)`
    """
    if not df_event.index.is_monotonic_increasing:
        df_event.sort_index(inplace=True)
    if not df.index.is_monotonic_increasing:
        df.sort_index(inplace=True)
    primary_pids = df_event["particle_id"].unique()
    energy_slopes = df_run["energy_spectrum_slope"].unique()
    emaxs = df_run["energy_max"].unique()
    emins = df_run["energy_min"].unique()

    assert len(energy_slopes) == 1
    assert len(emaxs) == 1
    assert len(emins) == 1
    energy_slope = energy_slopes[0]
    emin, emax = emins[0], emaxs[0]

    N = 1
    if energy_slope == -1:
        N = np.log(emax / emin)
    else:
        ep = energy_slope + 1
        N = (emax**ep - emin**ep) / ep

    weights = []
    for primary_pid in primary_pids:
        pdgid = Corsika7ID(primary_pid).to_pdgid()

        def flux(E: Any, id: PDGID = pdgid) -> Any:
            return model.flux(id, E, check_valid_pdgid=False)

        energy = df_event["total_energy"][df_event["particle_id"] == primary_pid]
        ext_pdf = energy.shape[0] * (energy**energy_slope) / N

        weights += [flux(energy) / ext_pdf]

    return pd.concat(weights)


def add_weight_prompt(
    df: pd.DataFrame,
    prompt_factor: float,
    weight_col_name: str = "weight_prompt",
    is_prompt_col_name: str = "is_prompt",
) -> None:
    """
    Adds column "weight_prompt" to df, to set a weight for every prompt particle, non prompt particles get weight 1
    """
    if not df.index.is_monotonic_increasing:
        df.sort_index(inplace=True)

    df[weight_col_name] = 1.0
    df.loc[
        df[is_prompt_col_name] == True, weight_col_name  # noqa: E712
    ] = prompt_factor


def add_weight_prompt_per_event(
    df: pd.DataFrame,
    prompt_factor: float,
    weight_col_name: str = "weight_prompt_per_event",
    is_prompt_col_name: str = "is_prompt",
) -> None:
    """
    Adds column "weight_prompt_per_event" to df, which will be `prompt_factor` for every particle, which is inside
    a shower, which has at least one prompt muon. For every other particle, it will be 1.
    """
    # For some weird reason this makes a difference, as the last line of this function does not work otherwise
    if not df.index.is_monotonic_increasing:
        df.sort_index(inplace=True)

    df[weight_col_name] = 1.0

    indexes = df.query(f"{is_prompt_col_name} == True").index
    evt_idxs: dict[int, set[Any]] = {i[0]: set() for i in indexes}
    for i in indexes:
        evt_idxs[i[0]].add(i[1])

    for i in evt_idxs:
        df.loc[i].loc[list(evt_idxs[i]), weight_col_name] = prompt_factor
