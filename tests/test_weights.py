from __future__ import annotations
from pathlib import Path

import numpy as np
import panama
import pandas as pd
import pytest
from click.testing import CliRunner
from corsikaio import CorsikaParticleFile
from panama.cli import cli
from particle.pdgid import literals
import fluxcomp
from fluxcomp import muon_fluxes

import matplotlib.pyplot as plt

SINGLE_TEST_FILE = Path(__file__).parent / "files" / "DAT000000"
GLOB_TEST_FILE = Path(__file__).parent / "files" / "DAT*"


def test_weight_wrong_arg(
    tmp_path,
    test_file_path=GLOB_TEST_FILE,
):
    df_run, df_event, df = panama.read_DAT(
        glob=test_file_path, drop_non_particles=False, mother_columns=True
    )

    with pytest.raises(ValueError, match="must be None"):
        ws = panama.get_weights(
            df_run,
            df_event,
            df,
            model=fluxcomp.H3a(),
            proton_only=True,
            groups={10: 10},
        )


def test_weight_overlapping_energy(
    tmp_path,
    test_file_path=GLOB_TEST_FILE,
):
    df_run, df_event, df = panama.read_DAT(
        glob=test_file_path, drop_non_particles=False, mother_columns=True
    )

    df_run.loc[:1, "energy_max"] = 1e20

    with pytest.raises(ValueError, match="overlap and thus cannot be reweighted"):
        ws = panama.get_weights(
            df_run, df_event, df, model=fluxcomp.H3a(), proton_only=True
        )


def test_weight_groups(
    tmp_path,
    test_file_path=SINGLE_TEST_FILE,
):
    df_run, df_event, df = panama.read_DAT(
        glob=test_file_path, drop_non_particles=False, mother_columns=True
    )

    ws = panama.get_weights(
        df_run, df_event, df, model=fluxcomp.H3a(), proton_only=False,
        groups={literals.proton: (1, 100)}
    )

    df["weight"] = ws
    df_event["weight"] = ws

    # fit primary index to check if weighting failed
    sel = df_event
    bins = np.geomspace(
        np.min(sel["total_energy"]), np.max(sel["total_energy"]), 20
    )
    hist, bin_edges = np.histogram(
        sel["total_energy"], bins=bins, weights=sel["weight"]
    )
    hist /= bin_edges[1:] - bin_edges[:-1]
    empty = hist == 0
    log_e = np.log10((bin_edges[1:] + bin_edges[:-1]) / 2)
    # dont fit empty bins
    p, V = np.polyfit(log_e[~empty], np.log10(hist[~empty]), deg=1, cov=True)
    # test if fittet spectral index is between 2.7 and 3
    assert p[0] + np.sqrt(V[0, 0]) > -3.0 
    assert p[0] - np.sqrt(V[0, 0]) < -2.7

def test_weight_multiple_slopes(
    tmp_path,
    test_file_path=GLOB_TEST_FILE,
):
    df_run, df_event, df = panama.read_DAT(
        glob=test_file_path, drop_non_particles=False, mother_columns=True
    )

    df_run.loc[:1, "energy_spectrum_slope"] = 7

    with pytest.raises(
        ValueError,
        match=
        'There are multiple energy slopes in the dataframe and thus they cannot be reweighted with this code.'
    ):
        ws = panama.get_weights(
            df_run, df_event, df, model=fluxcomp.H3a(), proton_only=True
        )


def test_weight_slope_2(
    tmp_path,
    test_file_path=GLOB_TEST_FILE,
):
    df_run, df_event, df = panama.read_DAT(
        glob=test_file_path, drop_non_particles=False, mother_columns=True
    )

    df_run.loc[:, "energy_spectrum_slope"] = 2

    ws = panama.get_weights(
        df_run, df_event, df, model=fluxcomp.H3a(), proton_only=False
    )

    df["weight"] = ws
    df_event["weight"] = ws

    # fit primary index to check if weighting failed
    sel = df_event
    bins = np.geomspace(
        np.min(sel["total_energy"]), np.max(sel["total_energy"]), 20
    )
    hist, bin_edges = np.histogram(
        sel["total_energy"], bins=bins, weights=sel["weight"]
    )
    hist /= bin_edges[1:] - bin_edges[:-1]
    empty = hist == 0
    log_e = np.log10((bin_edges[1:] + bin_edges[:-1]) / 2)
    # dont fit empty bins
    p, V = np.polyfit(log_e[~empty], np.log10(hist[~empty]), deg=1, cov=True)
    # test if fittet spectral index is between 2.7 and 3
    assert p[0] + np.sqrt(V[0, 0]) < -3.0 or p[0] - np.sqrt(V[0, 0]) > -2.7

