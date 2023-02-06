from pathlib import Path

from corsika_tools import read_corsika_particle_files_to_dataframe
from corsikaio import CorsikaParticleFile


def test_read_corsia_file(test_file_path=Path(__file__).parent / "files" / "DAT000000"):

    df_run, df_header, df = read_corsika_particle_files_to_dataframe([test_file_path])

    with CorsikaParticleFile(test_file_path) as cf:
        num = 0
        for event in cf:
            for particle in event.particles:
                if particle["particle_description"] < 0:
                    num += 1
                    continue
                assert df.iloc[num]["px"] == particle["px"]
                num += 1
