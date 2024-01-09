"""
Functions to add weights to a CORSIKA dataframe read in by `read_DAT`.
If using the suggested flux definitions from `fluxcomp`, all fluxes
are given in units of :math:`(\mathrm{m^2}\ \mathrm{s}\ \mathrm{sr}\ \mathrm{GeV})^{-1}`.

"""  # noqa: W605
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from fluxcomp import CosmicRayFlux, H3a
from particle import PDGID, Corsika7ID

from .constants import PDGID_PROTON_1

DEFAULT_FLUX = H3a()


def get_weights(
    df_run: pd.DataFrame,
    df_event: pd.DataFrame,
    df: pd.DataFrame,
    model: CosmicRayFlux = DEFAULT_FLUX,
    proton_only: bool = False,
    groups: dict[PDGID, tuple[int, int]] | None = None,
) -> pd.DataFrame:
    """
    Returns a DataFrame with the correct weight for a given primary model
    The DataFrame will be indexed by the run and event index, so it can be
    assigned as a column to the particle DataFrame df.

    The primary energy can have different energy-regions, but they must not overlap,
    if they do, an error is raised.

    Parameters
    ----------
    df_run: The run dataframe (as returned by `panama.read_DAT`)
    df_event: The event dataframe (as returned by `panama.read_DAT`)
    df: The particle dataframe (as returned by `panama.read_DAT`)
    model: The Cosmic Ray primary flux model (instance of CRFlux from the FluxComp package)
    proton_only: If set to true (default is false), only proton pdgid weights are non-zero and refer to
        all-nucleon flux.
    groups: Mapping from the primary PDGID in the monte carlo, to an (inclusive) range of elements (represented by their atomic number) which will we summed up in the
        model to represent this element in MC. (values: Tuple[Zmin, Zmax])

    Returns
    -------
    weights: A dataframe with the weights labeled by the run and event index.

    Can be used like this: `df['weights'] = panama.get_weights(df_run, df_event, df)`
    """
    if groups is not None and proton_only is True:
        raise ValueError("if proton_only is true, groups must be None")

    if not df_event.index.is_monotonic_increasing:
        df_event.sort_index(inplace=True)
    if not df.index.is_monotonic_increasing:
        df.sort_index(inplace=True)
    primary_pids = df_event["particle_id"].unique()
    energy_slopes = df_run["energy_spectrum_slope"].unique()

    e_intervals = [
        pd.Interval(low, high)
        for low, high in np.unique(
            df_run.loc[:, ("energy_min", "energy_max")].to_numpy(), axis=0
        )
    ]

    # check if the energy intervals overlap, then this code won't work
    for idx, int1 in enumerate(e_intervals[:-1]):
        for int2 in e_intervals[idx + 1 :]:
            if int1.overlaps(int2):
                raise ValueError(
                    f"The energy intervals {int1} and {int2} in the dataframe overlap and thus cannot be reweighted, with this code."
                )

    if len(energy_slopes) != 1:
        raise ValueError(
            "There are multiple energy slopes in the dataframe and thus they cannot be reweighted with this code."
        )
    energy_slope = energy_slopes[0]

    weights = []

    for interval in e_intervals:
        emin, emax = interval.left, interval.right

        N = 1
        if energy_slope == -1:
            N = np.log(emax / emin)
        else:
            ep = energy_slope + 1
            N = (emax**ep - emin**ep) / ep

        for primary_pid in primary_pids:
            mask = (
                (df_event["particle_id"] == primary_pid)
                & (df_event["energy_min"] == emin)
                & (df_event["energy_max"] == emax)
            )

            pdgid = Corsika7ID(primary_pid).to_pdgid()

            if proton_only and pdgid != PDGID_PROTON_1:
                w = df_event["total_energy"][mask]
                w[:] = 0
                weights += [w]
                continue

            energy = df_event["total_energy"][mask]
            ext_pdf = energy.shape[0] * (energy**energy_slope) / N

            if proton_only:
                weights += [sum(model.total_p_and_n_flux(energy)) / ext_pdf]
            elif groups is None:
                weights += [
                    model.flux(pdgid, energy, check_valid_pdgid=False) / ext_pdf
                ]
            else:
                fluxes = []
                for model_pdgid in model.validPDGIDs:
                    if groups[pdgid][0] <= model_pdgid.Z <= groups[pdgid][1]:
                        fluxes += [
                            model.flux(model_pdgid, energy, check_valid_pdgid=True)
                        ]
                weights += [sum(fluxes) / ext_pdf]

    return pd.concat(weights)


def add_weight_prompt(
    df: pd.DataFrame,
    prompt_factor: float,
    weight_col_name: str = "weight_prompt",
    is_prompt_col_name: str = "is_prompt",
) -> None:
    """
    Adds column "weight_prompt" to df, to set a weight for every prompt particle, non prompt particles get weight 1.

    Parameters
    ----------
    df: The particle dataframe (as returned by `panama.read_DAT`)
    prompt_factor: The number to put in the `weight_prompt` column.
    weight_col_name: The column name to give for the prompt weight column (default 'weight_prompt').
    is_prompt_col_name: The name of the column which indicates the promptness of a particle.
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

    Parameters
    ----------
    df: The particle dataframe (as returned by `panama.read_DAT`)
    prompt_factor: The number to put in the `weight_prompt` column.
    weight_col_name: The column name to give for the prompt weight column (default 'weight_prompt_per_event').
    is_prompt_col_name: The name of the column which indicates the promptness of a particle (default: 'is_prompt').
    """
    # For some weird reason this makes a difference, as the last line of this function does not work otherwise
    if not df.index.is_monotonic_increasing:  # pragma: no cover
        df.sort_index(inplace=True)

    df[weight_col_name] = 1.0

    indexes = df.query(f"{is_prompt_col_name} == True").index
    evt_idxs: dict[int, set[Any]] = {i[0]: set() for i in indexes}
    for i in indexes:
        evt_idxs[i[0]].add(i[1])

    for i in evt_idxs:
        df.loc[i].loc[list(evt_idxs[i]), weight_col_name] = prompt_factor
