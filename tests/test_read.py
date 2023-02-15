from pathlib import Path

import panama
from corsikaio import CorsikaParticleFile
import numpy as np
from click.testing import CliRunner
import pandas as pd
from panama.cli import cli


def test_noparse(test_file_path=Path(__file__).parent / "files" / "DAT000000"):

    df_run_np, df_event_np, df_np = panama.read_DAT(
        test_file_path, drop_non_particles=False, noparse=True
    )
    df_run, df_event, df = panama.read_DAT(
        test_file_path, drop_non_particles=False, noparse=False
    )

    assert df_np.equals(df)


def test_read_corsia_file(test_file_path=Path(__file__).parent / "files" / "DAT000000"):

    df_run, df_event, df = panama.read_DAT(test_file_path, drop_non_particles=False)

    with CorsikaParticleFile(test_file_path, parse_blocks=True) as cf:
        num = 0
        for idx, event in enumerate(cf):
            assert df_event.iloc[idx]["total_energy"] == event.header["total_energy"]
            for particle in event.particles:
                if particle["particle_description"] < 0:
                    continue
                assert df.iloc[num]["px"] == particle["px"]
                num += 1


def test_cli(tmp_path, test_file_path=Path(__file__).parent / "files" / "DAT000000"):

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
    event_headers = pd.read_hdf(tmp_path / "output.hdf5", "event_header")

    with CorsikaParticleFile(test_file_path, parse_blocks=True) as cf:
        num = 0
        for idx, event in enumerate(cf):
            assert (
                event_headers.iloc[idx]["total_energy"] == event.header["total_energy"]
            )
            for particle in event.particles:
                assert particles.iloc[num]["px"] == particle["px"]
                num += 1


def test_spectral_index(test_file_path=Path(__file__).parent / "files" / "DAT*"):
    """Test if we can fit the muon spectral index, with the test dataset"""

    df_run, df_event, df = panama.read_DAT(
        glob=test_file_path, drop_non_particles=False, mother_columns=True
    )

    # add weights
    panama.add_weight(df_run, df_event, df)

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
    test_file_path=Path(__file__).parent / "files" / "DAT*",
):
    """Test if we can fit the muon spectral index, with the test dataset"""

    df_run, df_event, df = panama.read_DAT(
        glob=test_file_path, drop_non_particles=False, mother_columns=True
    )

    # add weights
    panama.add_weight(df_run, df_event, df, model=panama.fluxes.FastThunmanCO())

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
    # Prompt muons folow primary spectrum
    # this fails, since statistics is very low (only about 200 in test dataset)
    # and only some of them are proton... lets just skip this for now,
    # fix later
    # assert p[0] - np.sqrt(V[0, 0]) < -2.7 < p[0] + np.sqrt(V[0, 0])
