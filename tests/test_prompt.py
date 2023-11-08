from __future__ import annotations
from pathlib import Path

import numpy as np
import panama
import pandas as pd
import pytest

GLOB_TEST_FILE = Path(__file__).parent / "files" / "DAT*"

def test_prompt_definitions_similar(test_file_path=GLOB_TEST_FILE):
    """Tests if the different definitions of prompt are similar enough on the test dataset"""

    df_run, df_event, df = panama.read_DAT(
        glob=test_file_path, drop_non_particles=False, mother_columns=True, drop_mothers=True
    )

    prompt_baseline = df["is_prompt"].to_numpy()
    prompt_lifetime = panama.prompt.is_prompt_lifetime_limit(df)
    prompt_lifetime_cleaned = panama.prompt.is_prompt_lifetime_limit_cleaned(df)
    prompt_pion_kaon = panama.prompt.is_prompt_pion_kaon(df)
    prompt_energy = panama.prompt.is_prompt_energy(df, 10)
    prompt_grandmother = panama.prompt.is_prompt_pion_kaon_grandmother(df)

    assert np.sum(prompt_baseline != prompt_lifetime)/len(prompt_baseline) < 0.01
    assert np.sum(prompt_baseline != prompt_pion_kaon)/len(prompt_baseline) < 0.01
    assert np.sum(prompt_baseline != prompt_energy)/len(prompt_baseline) < 0.01
    assert np.sum(prompt_baseline != prompt_lifetime_cleaned)/len(prompt_baseline) < 0.01
    assert np.sum(prompt_baseline != prompt_grandmother)/len(prompt_baseline) < 0.01


def test_none_lifetime(test_file_path=GLOB_TEST_FILE):
    df_run, df_event, df = panama.read_DAT(
        glob=test_file_path, drop_non_particles=False, mother_columns=True, drop_mothers=True
    )

    df.loc[:, "mother_pdgid_cleaned"] = 3101 # whatever this particle is, it has None mass and lifetime


    panama.prompt.add_cleaned_mother_cols(df)

    assert None not in df["mother_lifetime_cleaned"]


def test_prompt_definitions_wrong(test_file_path=GLOB_TEST_FILE):
    """Tests if the 'wrong' definitions of prompt are deviating enough from the baseline on the test dataset."""

    df_run, df_event, df = panama.read_DAT(
        glob=test_file_path, drop_non_particles=False, mother_columns=True, drop_mothers=True
    )

    prompt_baseline = df["is_prompt"].to_numpy()
    prompt_energy_wrong = panama.prompt.is_prompt_energy_wrong_pdgid(df)
    prompt_pion_kaon_wrong = panama.prompt.is_prompt_pion_kaon_wrong_pdgid(df)

    assert 0.09 < np.sum(prompt_baseline != prompt_energy_wrong)/len(prompt_baseline) < 0.20
    assert 0.09 < np.sum(prompt_baseline != prompt_pion_kaon_wrong)/len(prompt_baseline) < 0.20


def test_weight_prompt(test_file_path=GLOB_TEST_FILE):
    df_run, df_event, df = panama.read_DAT(
        glob=test_file_path, drop_non_particles=False, mother_columns=True, drop_mothers=True
    )
    
    panama.add_weight_prompt(df, 137.420)
    panama.add_weight_prompt_per_event(df, 137.420)

    assert np.all(df.query("is_prompt == True")["weight_prompt_per_event"] == 137.420)
    assert np.all(df.query("is_prompt == True")["weight_prompt"] == 137.420)
