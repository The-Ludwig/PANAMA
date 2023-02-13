import click
import logging
from os import environ
from .parallel_run import run_corsika_parallel
from pathlib import Path

from .run import run
from .corsika_to_hdf5 import hdf5


@click.group([run, hdf5], context_settings={"show_default": True})
@click.option("--debug", "-d", default=False, is_flag=True, help="Enable debug output")
def cli(
    debug,
):
    """
    Command line interface for PANAMA, providing useful CORSIKA utilities.

    For examples see the PANAMA repository:

    https://github.com/The-Ludwig/PANAMA#readme
    """
    if debug:
        logging.basicConfig(level=logging.DEBUG)


if __name__ == "__main__":
    cli()
