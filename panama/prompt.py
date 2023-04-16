import numpy as np
import pandas as pd

from .constants import D0_LIFETIME, PDGID_ERROR_VAL


def is_prompt_lifetime_limit(
    df_particles: pd.DataFrame, lifetime_limit_ns: float = D0_LIFETIME * 10
) -> np.ndarray:
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


def is_prompt_pion_kaon(df_particles: pd.DataFrame) -> np.ndarray:
    """Return a numpy array of prompt labels for the input dataframe differentiating it by the pdgid (cleaned)
    of the mother particle. If the mother is a pion or a kaon it is not prompt, otherwise it is.

    Parameters
    ----------
    df_particles: dataframe with the corsika particles, additional_columns have to be present when running `read_DAT`

    Returns
    -------
    A numpy boolean array, True for prompt, False for conventional
    """

    is_prompt = np.ones(df_particles.shape[0], dtype=bool)

    pdgidc = np.abs(df_particles["mother_pdgid_cleaned"].to_numpy(copy=False))

    is_prompt[(pdgidc == 211) | (pdgidc == 321) | (pdgidc == PDGID_ERROR_VAL)] = False

    return is_prompt


def is_prompt_energy(df_particles: pd.DataFrame, s: float = 2) -> np.ndarray:
    """Return a numpy array of prompt labels for the input dataframe differentiating it by energy of the mother particle.

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
