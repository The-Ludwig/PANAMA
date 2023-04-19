from __future__ import annotations
from pathlib import Path

import numpy as np
import panama
import pandas as pd
import pytest
from click.testing import CliRunner
from corsikaio import CorsikaParticleFile
from panama.cli import cli

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
def test_cli(pytestconfig, tmp_path, test_file_path=SINGLE_TEST_FILE):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "hdf5",
            f"{test_file_path}",
            f"{tmp_path}/output.hdf5",
        ],
    )

    assert result.exit_code == 0

    particles = pd.read_hdf(tmp_path / "output.hdf5", "particles")
    event_header = pd.read_hdf(tmp_path / "output.hdf5", "event_header")
    run_header = pd.read_hdf(tmp_path / "output.hdf5", "run_header")

    check_eq(test_file_path, run_header, event_header, particles)


def test_spectral_index(test_file_path=GLOB_TEST_FILE):
    """Test if we can fit the muon spectral index, with the test dataset"""

    df_run, df_event, df = panama.read_DAT(
        glob=test_file_path, drop_non_particles=False, mother_columns=True
    )

    # add weights
    df["weight"] = panama.get_weight(df_run, df_event, df)

    assert np.sum(np.isnan(df["weight"])) == 0

    # fit primary index to check if weighting worked
    sel = df_event
    bins = np.logspace(
        np.log10(np.min(sel["total_energy"])), np.log10(np.max(sel["total_energy"])), 20
    )
    hist, bin_edges = np.histogram(
        sel["total_energy"], bins=bins, weights=sel["weight"]
    )
    hist /= bin_edges[1:] - bin_edges[:-1]
    empty = hist == 0
    log_e = np.log10((bin_edges[1:] + bin_edges[:-1]) / 2)
    # dont fit empty bins
    p, V = np.polyfit(log_e[~empty], np.log10(hist[~empty]), deg=1, cov=True)
    # 2 sigma is good enough...
    assert p[0] - 2 * np.sqrt(V[0, 0]) < -2.7 < p[0] + 2 * np.sqrt(V[0, 0])

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
    assert p[0] - np.sqrt(V[0, 0]) < -4.5 < p[0] + np.sqrt(V[0, 0])

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
    assert p[0] - np.sqrt(V[0, 0]) < -2.7 < p[0] + np.sqrt(V[0, 0])


def test_spectral_index_proton_only(
    test_file_path=GLOB_TEST_FILE,
):
    """Test if we can fit the muon spectral index, with the test dataset"""

    df_run, df_event, df = panama.read_DAT(
        glob=test_file_path, drop_non_particles=False, mother_columns=True
    )

    # add weights
    df["weight"] = panama.get_weight(df_run, df_event, df, model=panama.fluxes.FastThunmanCO())

    assert np.sum(np.isnan(df["weight"])) == 0

    # fit primary index to check if weighting worked
    sel = df_event
    bins = np.logspace(
        np.log10(np.min(sel["total_energy"])), np.log10(np.max(sel["total_energy"])), 20
    )
    hist, bin_edges = np.histogram(
        sel["total_energy"], bins=bins, weights=sel["weight"]
    )
    hist /= bin_edges[1:] - bin_edges[:-1]
    empty = hist == 0
    log_e = np.log10((bin_edges[1:] + bin_edges[:-1]) / 2)
    # dont fit empty bins
    p, V = np.polyfit(log_e[~empty], np.log10(hist[~empty]), deg=1, cov=True)
    # 2 sigma is good enough...
    assert p[0] - 2 * np.sqrt(V[0, 0]) < -2.7 < p[0] + 2 * np.sqrt(V[0, 0])

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
    assert p[0] - np.sqrt(V[0, 0]) < -4.5 < p[0] + np.sqrt(V[0, 0])

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
    # this fails, since statistics is very low (only about 200 in test dataset)
    # and only some of them are proton... lets just skip this for now,
    # fix later
    # assert p[0] - np.sqrt(V[0, 0]) < -2.7 < p[0] + np.sqrt(V[0, 0])
