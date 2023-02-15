import click
import logging
from os import environ
from pathlib import Path
from .read import read_DAT


@click.command(context_settings={"show_default": True})
@click.argument("input", type=click.Path(exists=True, dir_okay=False), nargs=-1)
@click.argument("output", type=click.Path(exists=False, dir_okay=False), nargs=1)
@click.option(
    "--noadd",
    "-n",
    is_flag=True,
    help="Don't parse Corsika information into additional collumns like e.g. pdgid.",
)
@click.option(
    "--mother",
    "-m",
    is_flag=True,
    help="Parse mother information into additional collumns if they are provided with the EHIST option of CORSIKA",
)
@click.option(
    "--dropMother",
    "-dm",
    is_flag=True,
    help="Drop mother particles that don't reach observation level. (EHIST)",
)
@click.option(
    "--dropNonParticles",
    "-dp",
    is_flag=True,
    help="Drop all rows which don't really represent a particle. (Like decay or additional information)",
)
def hdf5(
    input: [Path],
    output: Path,
    noadd: bool,
    mother: bool,
    dropmother: bool,
    dropnonparticles: bool,
):
    """
    Convert CORSIKA7 DAT files to hdf5 files.

    INPUT: One or more CORSIKA7 datfiles
    OUTPUT: The filename of the hdf5 output file

    For examples see the PANAMA repository:

    https://github.com/The-Ludwig/PANAMA#readme
    """

    files = list(input)

    run_header, event_header, particles = read_DAT(
        files=files,
        additional_columns=not noadd,
        mother_columns=mother,
        drop_mothers=dropmother,
        drop_non_particles=dropnonparticles,
    )

    run_header.to_hdf(output, "run_header")
    event_header.to_hdf(output, "event_header")
    particles.to_hdf(output, "particles")
