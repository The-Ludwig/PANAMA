import click
import logging
from os import environ
from pathlib import Path
from .read import read_DAT


@click.command(context_settings={"show_default": True})
@click.argument("datfiles", type=click.Path(exists=True, dir_okay=False), nargs=-1)
@click.argument("hdf5out", type=click.Path(exists=False, dir_okay=False, nargs=1))
@click.option("--noadd", is_flag=True)
def corsika_to_hdf5(
    datfiles: [Path],
    output: Path,
    no_additional_collumns: bool,
    no_mother_columns: bool,
    drop_mothers: bool,
    drop_non_particles: bool,
):
    """
    Command line interface to convert CORSIKA7 DAT files to hdf5 files.

    For examples see the PANAMA repository:

    https://github.com/The-Ludwig/PANAMA#readme
    """

    run_header, event_header, particles = read_DAT(
        files=datfiles,
        additional_columns=additional_columns,
        mother_columns=mother_columns,
        drop_mothers=drop_mothers,
        drop_non_particles=drop_non_particle,
    )
