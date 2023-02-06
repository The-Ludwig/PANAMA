from pathlib import Path

import panama
from corsikaio import CorsikaParticleFile


def test_read_corsia_file(test_file_path=Path(__file__).parent / "files" / "DAT000000"):

    df_run, df_header, df = panama.read_DAT(test_file_path, drop_non_particles=False)

    with CorsikaParticleFile(test_file_path) as cf:
        num = 0
        for event in cf:
            for particle in event.particles:
                if particle["particle_description"] < 0:
                    continue
                assert df.iloc[num]["px"] == particle["px"]
                num += 1
