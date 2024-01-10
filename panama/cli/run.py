from __future__ import annotations

import logging
from os import environ
from pathlib import Path
from typing import Any

import click

from ..run import CorsikaRunner
from ..version import __logo__

DEFAULT_TMP_DIR = environ.get("TMP_DIR", "/tmp/PANAMA")
CORSIKA_PATH = environ.get(
    "CORSIKA_PATH",
    f"{environ.get('HOME')}/corsika7-master/run/corsika77420Linux_SIBYLL_urqmd",
)
DEFAULT_N_EVENTS = 100


class IntOrDictParamType(click.ParamType):  # type: ignore[misc]
    name = "int or py dict"

    def convert(self, value: int | str, param: Any, ctx: Any) -> int | dict[int, int]:
        # this might be coverage-hacking, but the tutorial says
        # to write it this way, but apparently this won't be evaluated
        # even if ints are passed
        if isinstance(value, int):  # pragma: no cover
            return value

        try:
            d = eval(value)  # noqa: PGH001
            if not isinstance(d, (int, dict)):  # noqa: UP038
                self.fail(
                    f"{value!r} is a valid python expression, but not a dict nor an int",
                    param,
                    ctx,
                )
            return d
        except SyntaxError:
            self.fail(f"{value!r} is not a valid python expression", param, ctx)

        raise RuntimeError("Unreachable code")  # pragma: no cover


INT_OR_DICT = IntOrDictParamType()


@click.command(context_settings={"show_default": True})
@click.argument(
    "template", type=click.Path(exists=True, dir_okay=False)
)  # , help="Path to the template to run")
@click.option(
    "--events",
    "-n",
    type=int,
    help="Number of shower-events to generate per primary particle.",
    default=DEFAULT_N_EVENTS,
)
@click.option(
    "--primary",
    "-p",
    type=INT_OR_DICT,
    help="PDGid of primary to inject. Default is proton. "
    "Can be a python dict with different primaries as keys and values the number of events to generate for that. "
    "In this case, --events is ignored. "
    "Example with proton and iron: {2212: 100_000, 1000260560: 1000}",
    default=2212,
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Path to store the CORSIKA7 DAT files",
    default="./corsika_output/",
)
@click.option("--jobs", "-j", default=4, help="Number of jobs to use", type=int)
@click.option(
    "--corsika",
    "-c",
    default=CORSIKA_PATH,
    help="Path to the CORSIKA7 executable. Can also be set using the `CORSIKA_PATH` environment variable.",
    type=click.Path(exists=True, dir_okay=False, executable=True),
)
@click.option(
    "--seed",
    "-s",
    default=None,
    help="Seed to use. If none, will use system time or other entropic source",
    type=int,
)
@click.option(
    "--tmp",
    "-t",
    default=DEFAULT_TMP_DIR,
    type=click.Path(file_okay=False),
    help="Path to the default temp folder to copy corsika to, will be appended by _n if it is not empty. Can also be set using the `TMP_DIR` environment variable.",
)
@click.option(
    "--save-std",
    "-l",
    default=False,
    is_flag=True,
    help="Save CORSIKAs std_out to a log file in output directory.",
)
@click.option(
    "--first_run_number",
    "-fr",
    default=0,
    help="Sets the first run number, for multiple output files, the number increments from that number.",
    type=int,
)
@click.option(
    "--first_event_number",
    "-fe",
    default=1,
    help="Sets the first event number in each produced DAT file.",
    type=int,
)
@click.option("--debug", "-d", default=False, is_flag=True, help="Enable debug output")
def run(
    template: Path,
    events: int,
    primary: int | dict[int, int],
    output: Path,
    jobs: int,
    corsika: Path,
    seed: int,
    tmp: Path,
    save_std: bool,
    first_run_number: int,
    first_event_number: int,
    debug: bool,
) -> None:
    """
    Run CORSIKA7 in parallel.

    The `TEMPLATE` argument must point to a valid CORSIKA7 steering card, where
    `{run_idx}`, `{first_event_idx}` `{n_show}` `{seed_1}` `{seed_2}` and `{dir}`
    will be replaced accordingly.

    For examples see the PANAMA repository:

    https://github.com/The-Ludwig/PANAMA#readme
    """
    logger = logging.getLogger("panama")
    if debug:
        logging.basicConfig(level=logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.debug("debug log level activated")

    logger.info(__logo__)

    n = 0
    p = Path(tmp)
    while p.exists() and next(p.iterdir(), True) is not True:
        n += 1
        p = Path(DEFAULT_TMP_DIR + f"_{n}")

    if isinstance(primary, int):
        primary = {primary: events}
    elif events != DEFAULT_N_EVENTS:
        logger.warning(
            "Looks like --events was given and --primary was provided a dict. --events is ignored."
        )

    with CorsikaRunner(
        primary,
        jobs,
        template,
        Path(output),
        corsika,
        p,
        seed,
        save_std,
        first_run_number,
        first_event_number,
    ) as runner:
        runner.run()
