from pathlib import Path

import toml

from .cli import cli
from .constants import PDGID_ERROR_VAL
from .read import read_DAT
from .run import CorsikaRunner
from .weights import add_weight_prompt, add_weight_prompt_per_event, get_weights


def get_version() -> str:
    path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with open(path) as f:
        config = toml.loads(f.read())
    return config["tool"]["poetry"]["version"]


__version__ = get_version()

__all__ = (
    "read_DAT",
    "get_weights",
    "add_weight_prompt",
    "add_weight_prompt_per_event",
    "CorsikaRunner",
    "cli",
    "PDGID_ERROR_VAL",
    "__version__",
)
