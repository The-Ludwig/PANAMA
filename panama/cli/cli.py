import logging

import click

from .corsika_to_hdf5 import hdf5
from .run import run


@click.group()
@click.option("--debug", "-d", default=False, is_flag=True, help="Enable debug output")
def cli(
    debug: bool,
) -> None:
    """
    Command line interface for PANAMA, providing useful CORSIKA utilities.

    For examples see the PANAMA repository:

    https://github.com/The-Ludwig/PANAMA#readme
    """
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)


cli.add_command(hdf5)
cli.add_command(run)

if __name__ == "__main__":
    cli()
