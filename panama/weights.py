"""
Functions to add weights to the read in corsika dataframe
"""
from .fluxes import FastHillasGaisser2012


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
