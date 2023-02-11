from panama import run_corsika_parallel
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
    except OSError as e:
        print(dir(e))
        assert e.strerror == "Exec format error"
        assert e.errno == 8


def test_cli_missing_executable(
    test_file_path=Path(__file__).parent / "files" / "example_corsika.template",
):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            f"{test_file_path}",
            "--events",
            "10",
            "--primary",
            "{10: 10, 20: 20}",
            "--corsika",
            f"{test_file_path}",
        ],
    )
    assert "not executable" in result.output
    # assert "--events is ignored" in result.output
    assert result.exit_code == 2


def test_cli(
    test_file_path=Path(__file__).parent / "files" / "example_corsika.template",
    corsika_path=Path(__file__).parent.parent / "corsika-77420" / "run" / "corsika77420Linux_SIBYLL_urqmd",
    compare_files=Path(__file__).parent / "files" / "compare" / "DAT*"
):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            f"{test_file_path}",
            "--primary",
            "{2212: 1, 1000260560: 1}", # proton and iron
            "--corsika",
            f"{corsika_path}",
            "--output",
            "corsika_output",
            "--seed",
            "137",
            "--jobs",
            "1" # this also tests multi threading since we have one job per primary
        ]
    )
    
    assert "cleanup now" in result.output
    assert result.exit_code == 0
    
    run_header, event_header, ps = read_DAT(glob=compare_files)
    run_header_2, event_header_2, ps_2 = read_DAT(glob="corsika_output/DAT*")

    assert run_header.equals(run_header_2)
    assert event_header.equals(event_header_2)
    assert ps.equals(ps_2)

