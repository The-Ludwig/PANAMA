from __future__ import annotations
from pathlib import Path
from panama.cli import cli
from click.testing import CliRunner
from panama import read_DAT
import pytest

CORSIKA_VERSION = "corsika-77500"
CORSIKA_EXECUTABLE = "corsika77500Linux_SIBYLL_urqmd"

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


def test_cli_not_valid_python_fail(
    tmp_path,
    caplog,
    test_file_path=Path(__file__).parent / "files" / "example_corsika_low_energy.template",
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
            "{sdfs; s}", # proton
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

    assert result.exit_code == 2
    assert "Error: Invalid value for" in result.stdout 
    assert "not a valid python expression" in result.stdout 


def test_cli_not_a_dict(
    tmp_path,
    caplog,
    test_file_path=Path(__file__).parent / "files" / "example_corsika_low_energy.template",
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
            "[1, 2, 3]", # proton
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

    assert result.exit_code == 2
    assert "Error: Invalid value for" in result.stdout 
    assert "is a valid python expression, but not a dict" in result.stdout 


def test_cli_fast(
    tmp_path,
    caplog,
    test_file_path=Path(__file__).parent / "files" / "example_corsika_low_energy.template",
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
            "2212", # proton
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

    run_header_2, event_header_2, ps_2 = read_DAT(glob=f"{tmp_path}/DAT*")

    assert event_header_2.shape[0] == 1
    assert "DEBUG" in caplog.text


def test_cli_first_number(
    tmp_path,
    caplog,
    test_file_path=Path(__file__).parent / "files" / "example_corsika_low_energy.template",
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
            "2212", # proton
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
            "-fr",
            "42",
            "-fe",
            "420"
        ],
        catch_exceptions=False
    )

    assert result.exit_code == 0

    run_header_2, event_header_2, ps_2 = read_DAT(glob=f"{tmp_path}/DAT*")

    assert event_header_2.shape[0] == 1
    assert "DEBUG" in caplog.text
    assert event_header_2.index[0] == (42, 420)


def test_cli_double_arg(
    tmp_path,
    caplog,
    test_file_path=Path(__file__).parent / "files" / "example_corsika_low_energy.template",
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
            "{2212: 1}", # proton
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

    run_header_2, event_header_2, ps_2 = read_DAT(glob=f"{tmp_path}/DAT*")

    assert event_header_2.shape[0] == 1
    assert "DEBUG" in caplog.text
    assert "WARNING" in caplog.text
    assert "--events is ignored" in caplog.text


def test_cli_no_debug(
    tmp_path,
    caplog,
    test_file_path=Path(__file__).parent / "files" / "example_corsika_low_energy.template",
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
            "{2212: 1}",  # proton and iron
            "--corsika",
            f"{corsika_path}",
            "--output",
            f"{tmp_path}",
            "--seed",
            "137",
            "--jobs",
            "1",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0

    run_header_2, event_header_2, ps_2 = read_DAT(glob=f"{tmp_path}/DAT*")

    assert event_header_2.shape[0] == 1
    assert "DEBUG" not in caplog.text


def test_cli(
    tmp_path,
    caplog,
    test_file_path=Path(__file__).parent / "files" / "example_corsika.template",
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
            "{2212: 1, 1000260560: 1}",  # proton and iron
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

    run_header_2, event_header_2, ps_2 = read_DAT(glob=f"{tmp_path}/DAT*")

    assert event_header_2.shape[0] == 2
    assert "DEBUG" in caplog.text

