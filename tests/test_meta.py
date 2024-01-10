from panama import __logo__, __version__
from importlib.metadata import version
import importlib
import pytest
from click.testing import CliRunner
from panama.cli import cli
from pathlib import Path

SINGLE_TEST_FILE = Path(__file__).parent / "files" / "DAT000000"

def test_logo():
    logo = __logo__
    assert len(logo) > 500
    assert "v" in logo

def test_version():
    assert __version__ == version("corsika-panama").replace("+editable", "")


@pytest.mark.filterwarnings("ignore::pandas.errors.PerformanceWarning")
def test_cli_no_tables(pytestconfig, tmp_path, caplog, monkeypatch, test_file_path=SINGLE_TEST_FILE):
    monkeypatch.setattr(importlib.util, "find_spec", lambda s: None)

    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "hdf5",
            "--debug",
            f"{test_file_path}",
            f"{tmp_path}/output.hdf5",
        ],
        catch_exceptions=True
    )

    print(result.exception)
    assert type(result.exception) == ImportError
    assert "corsika-panama[hdf]" in result.exception.msg
    assert "corsika-panama[hdf]" in caplog.text
    assert result.exit_code == 1
