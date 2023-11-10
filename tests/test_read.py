from __future__ import annotations
from pathlib import Path

import numpy as np
import panama
from fluxcomp import muon_fluxes
import fluxcomp
import pandas as pd
import pytest
from click.testing import CliRunner
from corsikaio import CorsikaParticleFile
from panama.cli import cli

import matplotlib.pyplot as plt

SINGLE_TEST_FILE = Path(__file__).parent / "files" / "DAT000000"
GLOB_TEST_FILE = Path(__file__).parent / "files" / "DAT*"


def test_noparse(test_file_path=SINGLE_TEST_FILE):
    df_run_np, df_event_np, df_np = panama.read_DAT(
        test_file_path, drop_non_particles=False, noparse=True
    )
    df_run, df_event, df = panama.read_DAT(
        test_file_path, drop_non_particles=False, noparse=False
    )

    assert df_np.equals(df)


def test_mother_columns_later(test_file_path=SINGLE_TEST_FILE):
    df_run_1, df_event_1, df_1 = panama.read_DAT(
        test_file_path, drop_non_particles=False, mother_columns=True, drop_mothers=False
    )
    df_run_2, df_event_2, df_2 = panama.read_DAT(
        test_file_path, drop_non_particles=False, mother_columns=False, drop_mothers=False
    )

    panama.read.add_mother_columns(df_particles=df_2)

    assert df_1.equals(df_2)


def test_max_events(test_file_path=SINGLE_TEST_FILE):
    df_run, df_event, df = panama.read_DAT(
        test_file_path, max_events=2
    )

    assert len(df_event) == 2


def check_eq(file, df_run, df_event, particles, skip_mother=False):
    with CorsikaParticleFile(file, parse_blocks=True) as cf:
        num = 0
        for idx, event in enumerate(cf):
            assert df_event.iloc[idx]["total_energy"] == event.header["total_energy"]
            for particle in event.particles:
                if particle["particle_description"] < 0 and skip_mother:
                    continue
                assert particles.iloc[num]["px"] == particle["px"]
                num += 1


def test_noadd(test_file_path=SINGLE_TEST_FILE):
    with pytest.raises(ValueError, match="requires"):
        df_run, df_event, particles = panama.read_DAT(
            test_file_path, drop_non_particles=True, additional_columns=False
        )

    with pytest.raises(ValueError, match="requires"):
        df_run, df_event, particles = panama.read_DAT(
            test_file_path, drop_non_particles=False, mother_columns=True, additional_columns=False
        )


    df_run, df_event, particles = panama.read_DAT(
        test_file_path, drop_non_particles=False, additional_columns=True
    )

    check_eq(test_file_path, df_run, df_event, particles, skip_mother=True)


def test_read_corsia_file(test_file_path=SINGLE_TEST_FILE):
    df_run, df_event, df = panama.read_DAT(test_file_path, drop_non_particles=False)

    check_eq(test_file_path, df_run, df_event, df, skip_mother=True)
    try:
        check_eq(test_file_path, df_run, df_event, df, skip_mother=False)
        raise AssertionError()
    except AssertionError:
        pass


# Do not turn the PyTables performance warning into an error
@pytest.mark.filterwarnings("ignore::pandas.errors.PerformanceWarning")
def test_cli(pytestconfig, tmp_path, caplog, test_file_path=SINGLE_TEST_FILE):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "hdf5",
            "--debug",
            f"{test_file_path}",
            f"{tmp_path}/output.hdf5",
        ],
    )

    assert result.exit_code == 0

    particles = pd.read_hdf(tmp_path / "output.hdf5", "particles")
    event_header = pd.read_hdf(tmp_path / "output.hdf5", "event_header")
    run_header = pd.read_hdf(tmp_path / "output.hdf5", "run_header")

    check_eq(test_file_path, run_header, event_header, particles)

    assert "DEBUG" in caplog.text

def save_spectral_fit_test_fig(path, model, log_e, hist, p):
    empty = hist == 0
    x_plot = np.linspace(np.min(log_e[~empty]), np.max(log_e[~empty]), 1000)
    plt.plot(x_plot, p[1]+p[0]*x_plot, label="fit")
    plt.plot(log_e[~empty], np.log10(hist[~empty]), "x", label="weighted mc")
    plt.plot(x_plot, np.log10(model.total_flux(10.0**(x_plot))), ":", label="model")

    plt.xlabel("$\log \phi$")
    plt.ylabel("$\log E/GeV$")
    plt.legend()
    plt.savefig(path)
    plt.clf()


def test_read_none():
    with pytest.raises(ValueError, match="can't both be None"):
        df_run, df_event, df = panama.read_DAT()

    with pytest.raises(ValueError, match="can't both be not None"):
        df_run, df_event, df = panama.read_DAT(files = ["bla1", "bla2"], glob="bla*")

def test_spectral_index(tmp_path, test_file_path=GLOB_TEST_FILE):
    """Test if we can fit the muon spectral index, with the test dataset"""

    df_run, df_event, df = panama.read_DAT(
        glob=test_file_path, drop_non_particles=False, mother_columns=True
    )

    # add weights
    ws = panama.get_weights(df_run, df_event, df)
    df["weight"] = ws
    df_event["weight"] = ws

    assert np.sum(np.isnan(df["weight"])) == 0

    # fit primary index to check if weighting worked
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
    save_spectral_fit_test_fig(tmp_path/"test_fit_h3a.pdf", fluxcomp.H3a(), log_e, hist, p)
    # test if fittet spectral index is between 2.7 and 3
    assert p[0] + np.sqrt(V[0, 0]) > -3.0 
    assert p[0] - np.sqrt(V[0, 0]) < -2.7

    # fit conv muon spectral index in binned fit
    sel = df.query("abs(pdgid) == 13 & is_prompt == False & energy >= 1e4")
    bins = np.logspace(
        np.log10(np.min(sel["energy"])), np.log10(np.max(sel["energy"])), 20
    )
    hist, bin_edges = np.histogram(sel["energy"], bins=bins, weights=sel["weight"])
    hist /= bin_edges[1:] - bin_edges[:-1]
    empty = hist == 0
    log_e = np.log10((bin_edges[1:] + bin_edges[:-1]) / 2)
    # dont fit empty bins
    p, V = np.polyfit(log_e[~empty], np.log10(hist[~empty]), deg=1, cov=True)
    # conv muons follow primary spectrum -1
    save_spectral_fit_test_fig(tmp_path/"test_fit_h3a_conv.pdf", muon_fluxes.GaisserFlatEarth(), log_e, hist, p)
    assert p[0] + 2*np.sqrt(V[0, 0]) > -4.0 
    assert p[0] - 2*np.sqrt(V[0, 0]) < -3.7

    # fit prompt muon spectral index in binned fit
    sel = df.query("abs(pdgid) == 13 & is_prompt == True & energy >= 1e4")
    bins = np.logspace(
        np.log10(np.min(sel["energy"])), np.log10(np.max(sel["energy"])), 20
    )
    hist, bin_edges = np.histogram(sel["energy"], bins=bins, weights=sel["weight"])
    hist /= bin_edges[1:] - bin_edges[:-1]
    empty = hist == 0
    log_e = np.log10((bin_edges[1:] + bin_edges[:-1]) / 2)
    # dont fit empty bins
    p, V = np.polyfit(log_e[~empty], np.log10(hist[~empty]), deg=1, cov=True)
    # Prompt muons follow primary spectrum
    save_spectral_fit_test_fig(tmp_path/"test_fit_h3a_prompt.pdf", muon_fluxes.GaisserFlatEarthHighEnergy(), log_e, hist, p)
    assert p[0] + np.sqrt(V[0, 0]) > -3.0 
    assert p[0] - np.sqrt(V[0, 0]) < -2.7




def test_spectral_index_proton_only(
    tmp_path,
    test_file_path=GLOB_TEST_FILE,
):
    """Test if we can fit the muon spectral index, with the test dataset"""

    df_run, df_event, df = panama.read_DAT(
        glob=test_file_path, drop_non_particles=False, mother_columns=True
    )

    # add weights
    ws = panama.get_weights(df_run, df_event, df, model=fluxcomp.H3a(), proton_only=True)
    df["weight"] = ws
    df_event["weight"] = ws

    assert np.sum(np.isnan(df["weight"])) == 0

    # fit primary index to check if weighting worked
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
    
    save_spectral_fit_test_fig(tmp_path/"test_fit_proton_only.pdf", fluxcomp.TIGCutoff(), log_e, hist, p)
    assert p[0] + np.sqrt(V[0, 0]) > -3.1 
    assert p[0] - np.sqrt(V[0, 0]) < -2.8

    # fit conv muon spectral index in binned fit
    sel = df.query("abs(pdgid) == 13 & is_prompt == False & energy >= 1e4")
    bins = np.logspace(
        np.log10(np.min(sel["energy"])), np.log10(np.max(sel["energy"])), 20
    )
    hist, bin_edges = np.histogram(sel["energy"], bins=bins, weights=sel["weight"])
    hist /= bin_edges[1:] - bin_edges[:-1]
    empty = hist == 0
    log_e = np.log10((bin_edges[1:] + bin_edges[:-1]) / 2)
    # dont fit empty bins
    p, V = np.polyfit(log_e[~empty], np.log10(hist[~empty]), deg=1, cov=True)
    save_spectral_fit_test_fig(tmp_path/"test_fit_proton_only_conv.pdf", muon_fluxes.GaisserFlatEarth(), log_e, hist, p)
    # conv muons follow primary spectrum -1
    assert p[0] + 2*np.sqrt(V[0, 0]) > -4.0 
    assert p[0] - 2*np.sqrt(V[0, 0]) < -3.7

    # fit prompt muon spectral index in binned fit
    sel = df.query("abs(pdgid) == 13 & is_prompt == True & energy >= 1e4")
    bins = np.logspace(
        np.log10(np.min(sel["energy"])), np.log10(np.max(sel["energy"])), 20
    )
    hist, bin_edges = np.histogram(sel["energy"], bins=bins, weights=sel["weight"])
    hist /= bin_edges[1:] - bin_edges[:-1]
    empty = hist == 0
    log_e = np.log10((bin_edges[1:] + bin_edges[:-1]) / 2)
    # dont fit empty bins
    p, V = np.polyfit(log_e[~empty], np.log10(hist[~empty]), deg=1, cov=True)
    save_spectral_fit_test_fig(tmp_path/"test_fit_proton_only_prompt.pdf", muon_fluxes.GaisserFlatEarthHighEnergy(), log_e, hist, p)
    # Prompt muons follow primary spectrum
    assert p[0] + 3*np.sqrt(V[0, 0]) > -3.0 
    assert p[0] - 3*np.sqrt(V[0, 0]) < -2.7
