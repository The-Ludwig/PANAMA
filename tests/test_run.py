from __future__ import annotations
from panama import CorsikaRunner
from pathlib import Path
from panama.cli import cli
import subprocess
from click.testing import CliRunner
from panama import read_DAT


def test_run_fail(
    test_file_path=Path(__file__).parent / "files" / "example_corsika.template",
):
    try:
        run_corsika_parallel(
            {2212: 100_000, 1000260560: 1000},
            4,
            test_file_path,
            Path("/tmp/corsika_test_output"),
            test_file_path.parent.parent.parent / "panama" / "cli.py",
            Path("/tmp/corsika_tmp_dir"),
        )
        assert False
    except OSError as e:
        print(dir(e))
        assert e.strerror == "Exec format error"
        assert e.errno == 8


def test_corsika_runner(
    tmp_path,
    test_file_path=Path(__file__).parent / "files" / "example_corsika.template",
    corsika_path=Path(__file__).parent.parent
    / "corsika-77420"
    / "run"
    / "corsika77420Linux_SIBYLL_urqmd",
    compare_files=Path(__file__).parent / "files" / "compare" / "DAT*",
):
    runner = CorsikaRunner(primary={2212: 1, 1000260560: 1},
                           n_jobs=1,
                           template_path=test_file_path,
                           output=tmp_path,
                           corsika_path=corsika_path,
                           corsika_tmp_dir=tmp_path,
                           seed=137,
                           jobs_per_primary=False)
    
    runner.run()
    
    run_header_2, event_header_2, ps_2 = read_DAT(glob=f"{tmp_path}/DAT*")

    assert event_header_2.shape[0] == 2
    print(event_header_2.keys())
    assert len(event_header_2["particle_id"].unique()) == 2


def test_cli_missing_executable(
    test_file_path=Path(__file__).parent / "files" / "example_corsika.template",
):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            f"{test_file_path}",
            "--events",
            "10",
            "--primary",
            "{10: 10, 20: 20}",
            "--corsika",
            f"{test_file_path}",
            "--debug",
        ],
        catch_exceptions=False
    )

    assert "not executable" in result.output
    # assert "--events is ignored" in result.output
    assert result.exit_code == 2


def test_different_primary_type(
    tmp_path,
    test_file_path=Path(__file__).parent / "files" / "example_corsika.template",
    corsika_path=Path(__file__).parent.parent
    / "corsika-77420"
    / "run"
    / "corsika77420Linux_SIBYLL_urqmd",
    compare_files=Path(__file__).parent / "files" / "compare" / "DAT*",
):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            f"{test_file_path}",
            "--primary",
            "2212",  # gamma
            "--events",
            "1",
            "--corsika",
            f"{corsika_path}",
            "--output",
            f"{tmp_path}",
            "--seed",
            "137",
            "--jobs",
            "1",
            "--debug",
        ],
        catch_exceptions=False
    )

    assert result.exit_code == 0

    # run_header, event_header, ps = read_DAT(glob=compare_files)
    run_header_2, event_header_2, ps_2 = read_DAT(glob=f"{tmp_path}/DAT*")

    assert event_header_2.shape[0] == 1
    assert event_header_2["particle_id"].iloc[0] == 14


def test_job_per_primary(
    tmp_path,
    test_file_path=Path(__file__).parent / "files" / "example_corsika.template",
    corsika_path=Path(__file__).parent.parent
    / "corsika-77420"
    / "run"
    / "corsika77420Linux_SIBYLL_urqmd",
    compare_files=Path(__file__).parent / "files" / "compare" / "DAT*",
):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            f"{test_file_path}",
            "--primary",
            "{2212: 1, 1000260560: 1}",  # proton and iron
            "--corsika",
            f"{corsika_path}",
            "--output",
            f"{tmp_path}",
            "--seed",
            "137",
            "--jobs",
            "1",  # this also tests multi threading since we have one job per primary
            "--debug",
            "--jobs-per-primary"
        ],
        catch_exceptions=False
    )

    assert result.exit_code == 0

    # run_header, event_header, ps = read_DAT(glob=compare_files)
    run_header_2, event_header_2, ps_2 = read_DAT(glob=f"{tmp_path}/DAT*")

    # sadly, this does not seem to match on different machines
    # probably, corsika related
    # assert run_header.equals(run_header_2)
    # assert event_header.equals(event_header_2)
    # assert ps.equals(ps_2)

    assert event_header_2.shape[0] == 2
    print(event_header_2.keys())
    assert len(event_header_2["particle_id"].unique()) == 2


def test_cli(
    tmp_path,
    test_file_path=Path(__file__).parent / "files" / "example_corsika.template",
    corsika_path=Path(__file__).parent.parent
    / "corsika-77420"
    / "run"
    / "corsika77420Linux_SIBYLL_urqmd",
    compare_files=Path(__file__).parent / "files" / "compare" / "DAT*",
):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            f"{test_file_path}",
            "--primary",
            "{2212: 1, 1000260560: 1}",  # proton and iron
            "--corsika",
            f"{corsika_path}",
            "--output",
            f"{tmp_path}",
            "--seed",
            "137",
            "--jobs",
            "1",  # this also tests multi threading since we have one job per primary
            "--debug",
        ],
        catch_exceptions=False
    )

    assert result.exit_code == 0

    # run_header, event_header, ps = read_DAT(glob=compare_files)
    run_header_2, event_header_2, ps_2 = read_DAT(glob=f"{tmp_path}/DAT*")

    # sadly, this does not seem to match on different machines
    # probably, corsika related
    # assert run_header.equals(run_header_2)
    # assert event_header.equals(event_header_2)
    # assert ps.equals(ps_2)

    assert event_header_2.shape[0] == 2
    print(event_header_2.keys())
    assert len(event_header_2["particle_id"].unique()) == 2
