#!/usr/bin/env python3
from subprocess import Popen, PIPE, TimeoutExpired
from os import environ
from pathlib import Path
from random import randrange
from random import seed as set_seed
import logging
from tqdm import tqdm
from time import sleep
import shutil
from .nbstreamreader import NonBlockingStreamReader as NBSR
from particle import Corsika7ID

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
    primary_corsikaid: int,
    first_event_idx: int = 1,
) -> Popen:
    # create dir if not existent
    output.mkdir(parents=True, exist_ok=True)

    corsika_copy_dir = corsika_tmp_dir / f".corsika_copy_run_{run_idx}"
    corsika_copy_dir.mkdir(parents=True, exist_ok=True)

    # copy all files in the corsika run dir, except for the DAT files
    # which are often created, if you test corsika in the run dir
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
                primary=f"{primary_corsikaid}",
            ).encode("ASCII"),
            timeout=1,
        )
    except TimeoutExpired:
        # this is what is expected...
        # Feels like a hack...
        pass
    return job


def cleanup(n_runs: int, corsika_tmp_dir: Path):
    for i in range(n_runs):
        shutil.rmtree(corsika_tmp_dir / f".corsika_copy_run_{i}")


def run_corsika_parallel(
    primary: dict,
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

    abs_path = Path(corsika_path).absolute()
    jobs: [Popen] = []

    for idx, (pdgid, n_events) in enumerate(primary.items()):
        corsikaid = int(Corsika7ID.from_pdgid(pdgid))

        events_per_job = n_events // n_jobs
        last_events_per_job = events_per_job + (n_events - events_per_job * n_jobs)

        for i in range(n_jobs - 1):
            jobs.append(
                start_corsika_job(
                    n_jobs * idx + i,
                    events_per_job,
                    input_template,
                    abs_path,
                    output,
                    corsika_tmp_dir,
                    corsikaid,
                )
            )
        jobs.append(
            start_corsika_job(
                n_jobs * idx + (n_jobs - 1),
                last_events_per_job,
                input_template,
                abs_path,
                output,
                corsika_tmp_dir,
                corsikaid,
            )
        )

    n_events = sum(primary.values())

    # show progressbar until close to end
    finished_events = 0
    nbstreams = [NBSR(job.stdout) for job in jobs]
    outputs = [b""] * len(jobs)

    try:
        with tqdm(total=n_events, unit="shower", unit_scale=True) as pbar:
            for job in jobs:
                while job.poll() is None:
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
    except KeyboardInterrupt:
        print("Interrupted by user, cleanup tmp files.")
        cleanup(n_jobs * len(primary), corsika_tmp_dir)

    # finish
    print("Jobs finished, now we wait for them to exit")
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
    cleanup(n_jobs * len(primary), corsika_tmp_dir)
