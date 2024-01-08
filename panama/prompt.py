"""
Functions to use to determine if a particle is prompt or not,
using multiple different definitions.
"""
from __future__ import annotations

from math import inf

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike
from particle import Particle

from .constants import D0_LIFETIME, PDGID_ERROR_VAL, PDGIDS_PION_KAON


def is_prompt_lifetime_limit(
    df_particles: pd.DataFrame, lifetime_limit_ns: float = D0_LIFETIME * 10
) -> ArrayLike:
    """Return a numpy array of prompt labels for the input dataframe differentiating it by the lifetime of the mother particle.

    Parameters
    ----------
    df_particles: dataframe with the corsika particles, additional_columns have to be present when running `read_DAT`
    lifetime_limit_ns:
        The lifetime limit in nanoseconds above which a particle is considered conventional.

    Returns
    -------
    A numpy boolean array, True for prompt, False for conventional
    """

    dif = df_particles["hadron_gen"].to_numpy(copy=False) - df_particles[
        "mother_hadr_gen"
    ].to_numpy(copy=False)

    return df_particles["has_mother"].to_numpy(copy=False) & (
        (
            (df_particles["mother_lifetimes"].to_numpy(copy=False) <= lifetime_limit_ns)
            & (
                (
                    np.abs(dif)
                    <= 1 & ~df_particles["mother_is_resonance"].to_numpy(copy=False)
                )
                # np.abs because of some very weird stuff going on in ehist
                | ((dif == 30) & df_particles["mother_has_charm"].to_numpy(copy=False))
            )
        )
        | (
            (df_particles["mother_pdgid"].abs().to_numpy(copy=False) == 13)
            & (df_particles["hadron_gen"] < 3)
        )  # mother is muon (and in early generation)
    )


def add_cleaned_mother_cols(df_particles: pd.DataFrame) -> None:
    """
    Adds mother_lifetime_cleaned, mother_mass_cleaned and mother_energy_cleaned if not present in the dataframe.
    """
    if "mother_lifetime_cleaned" not in df_particles:
        pdgids = df_particles["mother_pdgid_cleaned"].unique()
        lifetimes = {
            pdgid: Particle.from_pdgid(pdgid).lifetime
            if pdgid != PDGID_ERROR_VAL
            else inf
            for pdgid in pdgids
        }
        for pdgid in lifetimes:
            if lifetimes[pdgid] is None:
                lifetimes[pdgid] = 0

        df_particles["mother_lifetime_cleaned"] = (
            df_particles["mother_pdgid_cleaned"].map(lifetimes, na_action=None).array
        )

    if "mother_mass_cleaned" not in df_particles:
        pdgids = df_particles["mother_pdgid_cleaned"].unique()
        masses = {
            pdgid: Particle.from_pdgid(pdgid).mass if pdgid != PDGID_ERROR_VAL else 0
            for pdgid in pdgids
        }
        for pdgid, mass in masses.items():
            mass_ = mass
            if mass is None:
                mass_ = 0
            masses[pdgid] = mass_ / 1000

        df_particles["mother_mass_cleaned"] = (
            df_particles["mother_pdgid_cleaned"].map(masses, na_action=None).array
        )

    if "mother_energy_cleaned" not in df_particles:
        energy_cleaned = df_particles["mother_energy"].to_numpy(copy=False)
        energy_cleaned[
            df_particles["mother_pdgid_cleaned"].to_numpy(copy=False) == PDGID_ERROR_VAL
        ] = inf
        df_particles["mother_energy_cleaned"] = energy_cleaned


def is_prompt_lifetime_limit_cleaned(
    df_particles: pd.DataFrame, lifetime_limit_ns: float = D0_LIFETIME * 10
) -> ArrayLike:
    """Return a numpy array of prompt labels for the input dataframe differentiating it by lifetime of the mother particle.
    It considers the cleaned particle type of the mother.

    Parameters
    ----------
    df_particles: dataframe with the corsika particles, additional_columns have to be present when running `read_DAT`

    Returns
    -------
    A numpy boolean array, True for prompt, False for conventional
    """
    add_cleaned_mother_cols(df_particles)

    is_prompt = np.ones(df_particles.shape[0], dtype=bool)

    lifetimes = df_particles["mother_lifetime_cleaned"].to_numpy(copy=False)

    is_prompt[lifetimes >= lifetime_limit_ns] = False

    return is_prompt


def is_prompt_energy(df_particles: pd.DataFrame, s: float = 2) -> ArrayLike:
    """Return a numpy array of prompt labels for the input dataframe differentiating it by energy of the mother particle,
       with considering the cleaned particle type of the mother.

    Parameters
    ----------
    df_particles: dataframe with the corsika particles, additional_columns have to be present when running `read_DAT`
    s: scaling factor. How much bigger does the decay length has to be compared to the interaction length

    Returns
    -------
    A numpy boolean array, True for prompt, False for conventional
    """
    add_cleaned_mother_cols(df_particles)

    energy_limit_conversion_factor = 21681.666  # GeV

    limit = (
        energy_limit_conversion_factor
        * df_particles["mother_mass_cleaned"]
        / df_particles["mother_lifetime_cleaned"]
        / s
    )

    is_prompt = df_particles["mother_energy_cleaned"].to_numpy(
        copy=False
    ) < limit.to_numpy(copy=False)

    return is_prompt


def is_abs_id_not_in(
    df_particles: pd.DataFrame, pdgids: list[int], pdgid_col: str
) -> ArrayLike:
    """Return a numpy array which is true if abs(pdgid_col) is not in pdgids, false otherwise.

    Parameters
    ----------
    df_particles: DataFrame
        dataframe with the corsika particles, additional_columns have to be present when running `read_DAT`
    pdgids: list[int]
        list of ints with the pdgids to check
    pdgid_col: str
        column to check if abs value is not equal to any value in pdgids

    Returns
    -------
    A numpy boolean array, True if abs value of col is not in pdgids, False otherwise
    """

    pdgidc = np.abs(df_particles[pdgid_col].to_numpy(copy=False))

    return ~np.isin(pdgidc.astype(int), pdgids)


def is_prompt_pion_kaon(df_particles: pd.DataFrame) -> ArrayLike:
    """Return a numpy array of prompt labels for the input dataframe differentiating it by the pdgid (cleaned)
    of the mother particle. If the mother is a pion or a kaon it is not prompt, otherwise it is.

    Parameters
    ----------
    df_particles: dataframe with the corsika particles, additional_columns have to be present when running `read_DAT`
    pion_kaon_pdgids

    Returns
    -------
    A numpy boolean array, True for prompt, False for conventional
    """
    return is_abs_id_not_in(df_particles, PDGIDS_PION_KAON, "mother_pdgid_cleaned")


def is_prompt_pion_kaon_wrong_pdgid(df_particles: pd.DataFrame) -> ArrayLike:
    """Return a numpy array of prompt labels for the input dataframe differentiating it by the pdgid (uncleaned)
    of the mother particle. If the mother is a pion or a kaon it is not prompt, otherwise it is.

    Parameters
    ----------
    df_particles: dataframe with the corsika particles, additional_columns have to be present when running `read_DAT`

    Returns
    -------
    A numpy boolean array, True for prompt, False for conventional
    """

    return is_abs_id_not_in(df_particles, PDGIDS_PION_KAON, "mother_pdgid")


def is_prompt_pion_kaon_grandmother(df_particles: pd.DataFrame) -> ArrayLike:
    """Return a numpy array of prompt labels for the input dataframe differentiating it by the pdgid (cleaned)
    of the mother particle. If the mother is a pion or a kaon it is not prompt, otherwise it is.

    Parameters
    ----------
    df_particles: dataframe with the corsika particles, additional_columns have to be present when running `read_DAT`

    Returns
    -------
    A numpy boolean array, True for prompt, False for conventional
    """

    pdgidc = np.abs(df_particles["mother_pdgid_cleaned"].to_numpy(copy=False))
    pdgidgm = np.abs(df_particles["grandmother_pdgid"].to_numpy(copy=False))

    return ~np.isin(pdgidc.astype(int), PDGIDS_PION_KAON) & ~np.isin(
        pdgidgm.astype(int), PDGIDS_PION_KAON
    )


def is_prompt_energy_wrong_pdgid(df_particles: pd.DataFrame, s: float = 2) -> ArrayLike:
    """Return a numpy array of prompt labels for the input dataframe differentiating it by energy of the mother particle (uncleaned).

    Parameters
    ----------
    df_particles: dataframe with the corsika particles, additional_columns have to be present when running `read_DAT`
    s: scaling factor. How much bigger does the decay length has to be compared to the interaction length

    Returns
    -------
    A numpy boolean array, True for prompt, False for conventional
    """

    energy_limit_conversion_factor = 21681.666  # GeV

    limit = (
        energy_limit_conversion_factor
        * df_particles["mother_mass"]
        / df_particles["mother_lifetimes"]
        / s
    )

    is_prompt = df_particles["mother_energy"].to_numpy(copy=False) < limit.to_numpy(
        copy=False
    )

    return is_prompt
