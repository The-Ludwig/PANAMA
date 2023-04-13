import numpy as np
import pandas as pd


def is_prompt_lifetime_limit(
    df_particles: pd.Dataframe, lifetime_limit_ns: float = D0_LIFETIME * 10
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

    return df_particles["has_mother"].values & (
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
