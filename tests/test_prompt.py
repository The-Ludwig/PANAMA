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
    prompt_pion_kaon = panama.prompt.is_prompt_pion_kaon(df)
    prompt_energy = panama.prompt.is_prompt_energy(df, 10)

    assert np.sum(prompt_baseline != prompt_lifetime)/len(prompt_baseline) < 0.01
    assert np.sum(prompt_baseline != prompt_pion_kaon)/len(prompt_baseline) < 0.01
    assert np.sum(prompt_baseline != prompt_energy)/len(prompt_baseline) < 0.15

