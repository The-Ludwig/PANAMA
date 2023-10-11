import toml
import panama 

from pathlib import Path


def get_version() -> str:
    path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with open(path) as f:
        config = toml.loads(f.read())
    return config["tool"]["poetry"]["version"]

def test_version():
    assert panama.__version__ == get_version()
