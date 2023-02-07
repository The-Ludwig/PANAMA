#!/usr/bin/env python3
from subprocess import Popen, PIPE, TimeoutExpired
from os import environ
from pathlib import Path
from random import randrange
from random import seed as set_seed
import click
import logging
from tqdm import tqdm
from time import sleep
import shutil
from .nbstreamreader import NonBlockingStreamReader as NBSR

CORSIKA_FILE_ERROR = "STOP FILOPN: FATAL PROBLEM OPENING FILE"
CORSIKA_EVENT_FINISHED = b"PRIMARY PARAMETERS AT FIRST INTERACTION POINT AT HEIGHT"
CORSIKA_RUN_END = b"END OF RUN"


def start_corsika_job(
    run_idx: int,
    n_show: int,
    input_template: str,
    abs_corsika_path: Path,
    output: Path,
    corsika_tmp_dir: Path,
    first_event_idx: int = 1,
) -> Popen:
    # create dir if not existent
    output.mkdir(parents=True, exist_ok=True)

    corsika_copy_dir = corsika_tmp_dir / f".corsika_copy_run_{run_idx}"
    corsika_copy_dir.mkdir(parents=True, exist_ok=True)

    for p in abs_corsika_path.parent.glob("[!DAT]*"):
        if not p.is_file():
            continue
        shutil.copy(str(p.absolute()), str((corsika_copy_dir / p.name).absolute()))
    this_corsika_path = corsika_copy_dir / abs_corsika_path.name

    job = Popen(
        this_corsika_path.absolute(),
        stdin=PIPE,
        stdout=PIPE,
        cwd=this_corsika_path.absolute().parent,
    )

    try:
        stdin, stdout = job.communicate(
            input=input_template.format(
                run_idx=f"{run_idx}",
                first_event_idx="1",
                n_show=f"{n_show}",
                dir=str(output.absolute()) + "/",
                seed_1=f"{randrange(1, 900_000_000)}",
                seed_2=f"{randrange(1, 900_000_000)}",
            ).encode("ASCII"),
            timeout=1,
        )
    except TimeoutExpired:
        # this is what is expected...
        # Feels like a hack...
        pass
    return job


def cleanup(n_jobs: int, corsika_tmp_dir: Path):
    for i in range(n_jobs):
        shutil.rmtree(corsika_tmp_dir / f".corsika_copy_run_{i}")


def run_corsika_parallel(
    n_events,
    n_jobs,
    template_path,
    output: Path,
    corsika_path,
    corsika_tmp_dir: Path,
    seed=None,
):
    if seed is not None:
        set_seed(seed)

    with open(template_path) as f:
        input_template: str = f.read()

    events_per_job = n_events // n_jobs
    last_events_per_job = events_per_job + (n_events - events_per_job * n_jobs)

    abs_path = Path(corsika_path).absolute()
    jobs: [Popen] = []
    for i in range(n_jobs - 1):
        jobs.append(
            start_corsika_job(
                i, events_per_job, input_template, abs_path, output, corsika_tmp_dir
            )
        )
    jobs.append(
        start_corsika_job(
            n_jobs - 1,
            last_events_per_job,
            input_template,
            abs_path,
            output,
            corsika_tmp_dir,
        )
    )

    # show progressbar until close to end
    finished_events = 0
    nbstreams = [NBSR(job.stdout) for job in jobs]
    outputs = [b""] * len(jobs)

    with tqdm(total=n_events, unit="shower", unit_scale=True) as pbar:
        while jobs[-1].poll() is None:
            for idx, nbstream in enumerate(nbstreams):
                line = nbstream.readline()
                if line is not None:
                    outputs[idx] = b""
                while line is not None:
                    logging.debug(line.decode("ASCII"))
                    logging.info(
                        f"finished events = {line.count(CORSIKA_EVENT_FINISHED)}"
                    )
                    pbar.update(line.count(CORSIKA_EVENT_FINISHED))
                    outputs[idx] += line
                    line = nbstream.readline()
            sleep(0.5)

    # finish
    print("Jobs should be nearly finished, now we wait for them to exit")
    for idx, job in enumerate(jobs):
        (last_stdout, last_stderr_data) = job.communicate()
        line = nbstreams[idx].readline()
        while line is not None:
            outputs[idx] += line
            line = nbstreams[idx].readline()
        outputs[idx] += last_stdout
        logging.debug(f"Output job {idx}:\n {outputs[idx].decode('ASCII')}")
        if CORSIKA_RUN_END not in outputs[idx]:
            logging.warning(
                f"Corsika Output:\n {outputs[idx].decode('ASCII')} \n'END OF RUN' not in corsika output. May indicate failed run. See the output above."
            )

    print("All jobs terminated, cleanup now")
    cleanup(n_jobs, corsika_tmp_dir)


DEFAULT_TMP_DIR = environ.get("TMP_DIR", "/tmp/PANAMA")
CORSIKA_PATH = environ.get(
    "CORSIKA_PATH",
    f"{environ.get('HOME')}/corsika7-master/run/corsika77420Linux_SIBYLL_urqmd",
)


@click.command(context_settings={"show_default": True})
@click.argument(
    "template", type=click.Path(exists=True, dir_okay=False)
)  # , help="Path to the template to run")
@click.option(
    "--events",
    "-n",
    type=int,
    help="Number of shower-events to generate",
    default=100,
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
    help="Path to the default temp folder to copy corsika to. Can also be set using the `TMP_DIR` environment variable.",
)
@click.option("--debug", "-d", default=False, is_flag=True, help="Enable debug output")
def cli(
    template: Path,
    events: int,
    output: Path,
    jobs: int,
    corsika: Path,
    seed: int,
    tmp: Path,
    debug,
):
    """
    Command line interface to run CORSIKA7 in parallel.

    The `TEMPLATE` argument must point to a valid CORSIKA7 stiring card, where
    `{run_idx}`, `{first_event_idx}` `{n_show}` `{seed_1}` `{seed_2}` and `{dir}`
    will be replaced accordingly.

    For examples see the PANAMA repository:

    https://github.com/The-Ludwig/PANAMA#readme
    """
    if debug:
        logging.basicConfig(level=logging.DEBUG)

    if tmp == DEFAULT_TMP_DIR:
        n = 0
        p = Path(tmp)
        while p.exists() and next(p.iterdir(), True) != True:
            n += 1
            p = Path(DEFAULT_TMP_DIR + f"_{n}")
    else:
        p = Path(tmp)

    run_corsika_parallel(events, jobs, template, Path(output), corsika, p, seed)


if __name__ == "__main__":
    cli()
