from __future__ import annotations
from panama import CorsikaRunner
from panama.run import CorsikaJob
from pathlib import Path
from panama.cli import cli
import subprocess
from click.testing import CliRunner
from panama import read_DAT
import pytest
import numpy as np

CORSIKA_VERSION = "corsika-77500"
CORSIKA_EXECUTABLE = "corsika77500Linux_SIBYLL_urqmd"


def test_corsika_runner_cleanup(
    test_file_path=Path(__file__).parent / "files" / "example_corsika.template",
):
    """
    Tests if cleanup of the runner works and a new CorsikaRunner objct 
    with the same tmp path can be constructed.
    """
    with CorsikaRunner(
            {2212: 100_000, 1000260560: 1000},
            4,
            test_file_path,
            Path("/tmp/corsika_test_output"),
            test_file_path.parent.parent.parent / "panama" / "cli" / "cli.py",
            Path("/tmp/corsika_tmp_dir"),
    ) as runner:
        pass
    
    runner = CorsikaRunner(
            {2212: 100_000, 1000260560: 1000},
            4,
            test_file_path,
            Path("/tmp/corsika_test_output"),
            test_file_path.parent.parent.parent / "panama" / "cli" / "cli.py",
            Path("/tmp/corsika_tmp_dir"),
        )
    runner.clean()

    runner = CorsikaRunner(
            {2212: 100_000, 1000260560: 1000},
            4,
            test_file_path,
            Path("/tmp/corsika_test_output"),
            test_file_path.parent.parent.parent / "panama" / "cli" / "cli.py",
            Path("/tmp/corsika_tmp_dir"),
        )

def test_run_fail(
    test_file_path=Path(__file__).parent / "files" /
    "example_corsika.template",
):
    try:
        runner = CorsikaRunner(
            {2212: 100_000, 1000260560: 1000},
            4,
            test_file_path,
            Path("/tmp/corsika_test_output"),
            test_file_path.parent.parent.parent / "panama" / "cli" / "cli.py",
            Path("/tmp/corsika_tmp_dir"),
        )
        runner.run()
        assert False
    except OSError as e:
        print(dir(e))
        assert e.strerror == "Exec format error"
        assert e.errno == 8


def test_no_double_run(
    tmp_path,
    test_file_path=Path(__file__).parent / "files" /
    "example_corsika.template",
    corsika_path=Path(__file__).parent.parent
    / CORSIKA_VERSION
    / "run"
    / CORSIKA_EXECUTABLE,
    compare_files=Path(__file__).parent / "files" / "compare" / "DAT*",
):
    runner = CorsikaRunner(primary={2212: 1, 1000260560: 1},
                           n_jobs=1,
                           template_path=test_file_path,
                           output=tmp_path,
                           corsika_executable=corsika_path,
                           corsika_tmp_dir=tmp_path,
                           seed=137,
                           save_std=True
                           )

    cfg = runner._get_corsika_config(0, 5, 13)
    runner.job_pool[0].start(cfg)

    with pytest.raises(RuntimeError, match="it's still running"):
        runner.job_pool[0].start(cfg)

    del runner.job_pool[0]


def test_corsika_runner(
    tmp_path,
    test_file_path=Path(__file__).parent / "files" /
    "example_corsika.template",
    corsika_path=Path(__file__).parent.parent
    / CORSIKA_VERSION
    / "run"
    / CORSIKA_EXECUTABLE,
    compare_files=Path(__file__).parent / "files" / "compare" / "DAT*",
):
    runner = CorsikaRunner(primary={2212: 1, 1000260560: 1},
                           n_jobs=1,
                           template_path=test_file_path,
                           output=tmp_path,
                           corsika_executable=corsika_path,
                           corsika_tmp_dir=tmp_path,
                           seed=137,
                           )

    runner.run()

    run_header_2, event_header_2, ps_2 = read_DAT(glob=f"{tmp_path}/DAT*")

    assert event_header_2.shape[0] == 2
    print(event_header_2.keys())
    assert len(event_header_2["particle_id"].unique()) == 2


def test_corsika_runner_first_numbers(
    tmp_path,
    test_file_path=Path(__file__).parent / "files" /
    "example_corsika_low_energy.template",
    corsika_path=Path(__file__).parent.parent
    / CORSIKA_VERSION
    / "run"
    / CORSIKA_EXECUTABLE,
    compare_files=Path(__file__).parent / "files" / "compare" / "DAT*",
):
    runner = CorsikaRunner(primary={2212: 1},
                           n_jobs=1,
                           template_path=test_file_path,
                           output=tmp_path,
                           corsika_executable=corsika_path,
                           corsika_tmp_dir=tmp_path,
                           seed=137,
                           first_run_number=42,
                           first_event_number=420
                           )

    runner.run()

    run_header, event_header, ps = read_DAT(glob=f"{tmp_path}/DAT*")

    assert event_header.shape[0] == 1
    assert len(event_header["particle_id"].unique()) == 1
    assert event_header.index[0] == (42, 420)

def test_corsika_job_no_join(
    tmp_path,
    test_file_path=Path(__file__).parent / "files" /
    "example_corsika_low_energy.template",
    corsika_path=Path(__file__).parent.parent
    / CORSIKA_VERSION
    / "run"
    / CORSIKA_EXECUTABLE,
    compare_files=Path(__file__).parent / "files" / "compare" / "DAT*",
):
    runner = CorsikaRunner(primary={2212: 1},
                           n_jobs=1,
                           template_path=test_file_path,
                           output=tmp_path,
                           corsika_executable=corsika_path,
                           corsika_tmp_dir=tmp_path,
                           seed=137,
                           )

    runner.run()

    with pytest.raises(RuntimeError, match="already"):
        runner.job_pool[0].join()


def test_corsika_error(
    tmp_path,
    caplog,
    test_file_path=Path(__file__).parent / "files" /
    "example_corsika_faulty.template",
    corsika_path=Path(__file__).parent.parent
    / CORSIKA_VERSION
    / "run"
    / CORSIKA_EXECUTABLE,
    compare_files=Path(__file__).parent / "files" / "compare" / "DAT*",
):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--debug",
            "run",
            f"{test_file_path}",
            "--primary",
            "2212",
            "-n",
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

    assert "indicate failed run" in caplog.text


def test_file_output_compare(
    tmp_path,
    test_file_path=Path(__file__).parent / "files" /
    "example_corsika.template",
    corsika_path=Path(__file__).parent.parent
    / CORSIKA_VERSION
    / "run"
    / CORSIKA_EXECUTABLE,
    compare_files=Path(__file__).parent / "files" / "compare" / "DAT*",
):
    runner = CorsikaRunner(primary={2212: 3},
                           n_jobs=1,
                           template_path=test_file_path,
                           output=tmp_path,
                           corsika_executable=corsika_path,
                           corsika_tmp_dir=tmp_path,
                           seed=137,
                           )

    runner.run()

    run_header_1, event_header_1, ps_1 = read_DAT(glob=compare_files)
    run_header_2, event_header_2, ps_2 = read_DAT(glob=f"{tmp_path}/DAT*")

    for df_1, df_2 in ((event_header_1, event_header_2), (run_header_1, run_header_2), (ps_1, ps_2)):
        # remove references to dates
        dates = list(filter(lambda name: "date" in str(name), df_1.columns))
        df_1.drop(dates, axis="columns", inplace=True)
        df_2.drop(dates, axis="columns", inplace=True)
        assert df_1.select_dtypes(exclude=['object']).equals(
            df_2.select_dtypes(exclude=['object']))


def test_different_primary_type(
    tmp_path,
    test_file_path=Path(__file__).parent / "files" /
    "example_corsika.template",
    corsika_path=Path(__file__).parent.parent
    / CORSIKA_VERSION
    / "run"
    / CORSIKA_EXECUTABLE,
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


def test_multi_job(
    tmp_path,
    test_file_path=Path(__file__).parent / "files" /
    "example_corsika.template",
    corsika_path=Path(__file__).parent.parent
    / CORSIKA_VERSION
    / "run"
    / CORSIKA_EXECUTABLE,
    compare_files=Path(__file__).parent / "files" / "compare" / "DAT*",
):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            f"{test_file_path}",
            "--primary",
            "{2212: 2, 1000260560: 2}",  # proton and iron
            "--corsika",
            f"{corsika_path}",
            "--output",
            f"{tmp_path}",
            "--seed",
            "137",
            "--jobs",
            "2",
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

    assert event_header_2.shape[0] == 4
    assert run_header_2.shape[0] == 4
    assert len(event_header_2["particle_id"].unique()) == 2


def test_multi_job_fail(
    tmp_path,
    test_file_path=Path(__file__).parent / "files" /
    "example_corsika.template",
    corsika_path=Path(__file__).parent.parent
    / CORSIKA_VERSION
    / "run"
    / CORSIKA_EXECUTABLE,
    compare_files=Path(__file__).parent / "files" / "compare" / "DAT*",
):
    runner = CliRunner()
    with pytest.raises(ValueError, match="n_jobs must be smaller or equa"):
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
                "2",
                "--debug",
            ],
            catch_exceptions=False
        )


def test_save_output(
    tmp_path,
    test_file_path=Path(__file__).parent / "files" /
    "example_corsika_low_energy.template",
    corsika_path=Path(__file__).parent.parent
    / CORSIKA_VERSION
    / "run"
    / CORSIKA_EXECUTABLE,
):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            f"{test_file_path}",
            "--primary",
            "{2212: 2}",  # proton and iron
            "--corsika",
            f"{corsika_path}",
            "--output",
            f"{tmp_path}",
            "--seed",
            "137",
            "--jobs",
            "2",
            "--debug",
            "--save-std"
        ],
        catch_exceptions=False
    )

    assert result.exit_code == 0

    logfile = Path(f"{tmp_path}/prim2212_job0.log")
    assert logfile.exists()

    with open(logfile) as lf:
        content = lf.read()

    assert "END OF RUN" in content


def test_run_multitemp(
    tmp_path,
    caplog,
    test_file_path=Path(__file__).parent / "files" /
    "example_corsika_low_energy.template",
    corsika_path=Path(__file__).parent.parent
    / CORSIKA_VERSION
    / "run"
    / CORSIKA_EXECUTABLE,
    compare_files=Path(__file__).parent / "files" / "compare" / "DAT*",
):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--debug",
            "run",
            f"{test_file_path}",
            "--primary",
            "2212",  # proton
            "-n",
            "1",
            "--corsika",
            f"{corsika_path}",
            "--output",
            f"{tmp_path}/1",
            "--tmp",
            f"{tmp_path}/tmp",
            "--seed",
            "137",
            "--jobs",
            "1",
            "--debug",
        ],
        catch_exceptions=False
    )

    with open(f"{tmp_path}/tmp/touch", "w") as file:
        file.write("I am touched")

    runner2 = CliRunner()
    result2 = runner2.invoke(
        cli,
        [
            "--debug",
            "run",
            f"{test_file_path}",
            "--primary",
            "2212",  # proton
            "-n",
            "1",
            "--corsika",
            f"{corsika_path}",
            "--output",
            f"{tmp_path}/2",
            "--tmp",
            f"{tmp_path}/tmp",
            "--seed",
            "69",
            "--jobs",
            "1",
            "--debug",
        ],
        catch_exceptions=False
    )

    assert result.exit_code == 0
    assert result2.exit_code == 0
    assert Path(f"{tmp_path}/tmp/touch").exists()

    run_header_1, event_header_1, ps_1 = read_DAT(glob=f"{tmp_path}/1/DAT*")
    run_header_2, event_header_2, ps_2 = read_DAT(glob=f"{tmp_path}/2/DAT*")

    assert event_header_1.shape[0] == 1
    assert event_header_2.shape[0] == 1
    assert not event_header_1.select_dtypes(exclude=["object"]).equals(
        event_header_2.select_dtypes(exclude=["object"]))
    assert "DEBUG" in caplog.text
