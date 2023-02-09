from panama import run_corsika_parallel
from pathlib import Path
from panama.cli import cli
import subprocess
from click.testing import CliRunner

# since I can not ship the corsika executable,
# for now I will only test if this fails
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


def test_cli(
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
