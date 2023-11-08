import logging

import click

from ..version import __logo__
from .corsika_to_hdf5 import hdf5
from .run import run


@click.group()
@click.option("--debug", "-d", default=False, is_flag=True, help="Enable debug output")
@click.version_option(version=__logo__)
def cli(debug: bool) -> None:
    """
    Command line interface for PANAMA, providing useful CORSIKA utilities.

    For examples see the PANAMA repository:

    https://github.com/The-Ludwig/PANAMA#readme
    """
    logger = logging.getLogger("panama")

    if debug:
        logging.basicConfig(level=logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.debug("debug log level activated")
    else:
        logger.setLevel(logging.INFO)
        logging.basicConfig(level=logging.INFO)


cli.add_command(hdf5)
cli.add_command(run)
