import numpy as np
import pandas as pd
from particle import Particle

D0_LIFETIME = Particle.from_name("D0").lifetime

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

    dif = (
        df_particles["hadron_gen"].to_numpy(copy=False)
        - df_particles["mother_hadr_gen"].to_numpy(copy=False)
    )

    return df_particles["has_mother"].to_numpy(copy=False) & (
        (
            (df_particles["mother_lifetimes"].to_numpy(copy=False) <= lifetime_limit_ns)
            & (
                (np.abs(dif) <= 1 & ~df_particles["mother_is_resonance"].to_numpy(copy=False))
                # np.abs because of some very weird stuff going on in ehist
                | ((dif == 30) & df_particles["mother_has_charm"].to_numpy(copy=False))
            )
        )
        | (
            (df_particles["mother_pdgid"].abs().to_numpy(copy=False) == 13)
            & (df_particles["hadron_gen"] < 3)
        )  # mother is muon (and in early generation)
    )
