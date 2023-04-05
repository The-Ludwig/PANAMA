#!/usr/bin/env python3
from __future__ import annotations

import logging
import shutil
from contextlib import suppress
from pathlib import Path
from random import randrange
from random import seed as set_seed
from subprocess import PIPE, Popen, TimeoutExpired
from time import sleep
from typing import Any

from particle import Corsika7ID, Particle
from tqdm import tqdm

from .nbstreamreader import NonBlockingStreamReader as NBSR

CORSIKA_FILE_ERROR = "STOP FILOPN: FATAL PROBLEM OPENING FILE"
CORSIKA_EVENT_FINISHED = b"PRIMARY PARAMETERS AT FIRST INTERACTION POINT AT HEIGHT"
CORSIKA_RUN_END = b"END OF RUN"


class CorsikaJob:
    def __init__(self, corsika_executable: Path, corsika_copy_dir: Path, card_template: str) -> None:
        
        self.corsika_copy_path = corsika_copy_path
        self.corsika_copy_path.mkdir(parents=True, exist_ok=False)
        self.card_template = card_template

        # copy all files in the corsika run dir, except for the DAT files
        # which are often created, if you test corsika in the run dir
        for p in self.corsika_executable.absolute().parent.glob("[!DAT]*"):
            if not p.is_file():
                continue
            shutil.copy(str(p.absolute()), str((corsika_copy_dir / p.name).absolute()))
        self.this_corsika_path = self.corsika_copy_dir / self.abs_corsika_path.name

        self.running = None
        self.config = None
        self.stream = None
        self.finished_showers = 0
        self.output = b""
        self.finished = []

    def __del__(self) -> None:
        shutil.rmtree(self.corsika_copy_dir)

    @property
    def is_finished(self):
        return self.running is None

    def start(self, corsika_config: dir[str, Any]) -> None:
        if self.running is not None:
            raise RuntimeError("Can't use this CorsikaJob, it's still running!")
         
        self.finished_showers = 0
        self.running = Popen(
            self.this_corsika_path.absolute(),
            stdin=PIPE,
            stdout=PIPE,
            cwd=self.this_corsika_path.absolute().parent,
        )

        self.config = corsika_config

        # this is what is expected...
        # Feels like a hack...
        with suppress(TimeoutExpired):
            stdin, stdout = job.communicate(
                input=self.card_template.format(**corsika_config).encode("ASCII"),
                timeout=1,
            )

        self.stream = NBSR(self.running.stdout)
    
    def poll(self) -> int | None:
        """ 
        Returns
        -------
        n_update: The number of showers finished since last poll or None if process is finished
        """
        if self.running is None:
            return None
        
        if (return_code := self.running.poll()) is not None:
            if return_code != 0:
                raise RuntimeError("Return code of corsika not 0 (should not be possible)")
            
            return self.join()

        finished = 0

        line = self.readline()
        if line is not None:
            self.output = b""
        while line is not None:
            logging.debug(line.decode("ASCII"))
            logging.info(
                f"finished events = {line.count(CORSIKA_EVENT_FINISHED)}"
            )
            finished += line.count(CORSIKA_EVENT_FINISHED)
            self.output += line
            line = self.stream.readline()
        
        self.finished_showers += finished

        return finished

    def join(self) -> int:
        """
        Returns
        -------
        n_update: The number of finished events in the last output
        """
        if self.running is None:
            raise RuntimeError("Job is already finished")

        (last_stdout, last_stderr_data) = self.running.communicate()
        line = self.stream.readline()

        finished = 0

        while line is not None:
            finished += line.count(CORSIKA_EVENT_FINISHED)
            self.output += line
            line = self.stream.readline()

        finished += last_stdout.count(CORSIKA_EVENT_FINISHED)
        self.output += last_stdout
        logging.debug(f"{self.output.decode('ASCII')}")

        if CORSIKA_RUN_END not in self.output:
            logging.warning(
                f"Corsika Output:\n {outputs[idx].decode('ASCII')} \n'END OF RUN' not in corsika output. May indicate failed run. See the output above."
            )
        
        self._reset()

        return finished

    def _reset(self):
        self.running = None
        self.config = None
        self.stream = None
        self.finished_showers = 0

class CorsikaRunner:

    def __init__(
        self,
        primary: dict[int, int],
        n_jobs: int,
        template_path: Path,
        output: Path,
        corsika_executable: Path,
        corsika_tmp_dir: Path,
        seed=None,
    ) -> None:
        """
        TODO: Good Docstring, Types

        Parameters
        ----------
        job_per_primary: Set to true if n_jobs is not a hard limit.
            Then no more than `n_jobs` will be started and the components
            will be processed after each other.
            If set to `false` there will be `n_jobs` started for every component
            in parallel. The maximum number of jobs running at the same time then
            is `n_jobs*len(primary)`
        """
        self.primary = primary
        self.n_jobs = n_jobs
        self.job_per_primary = job_per_primary
        self.output = output
        self.corsika_executable = corsika_executable
        self.corsika_tmp_dir = corsika_tmp_dir

        if seed is not None:
            set_seed(seed)
        self.seed = seed
        
        with open(template_path) as f:
            self.input_template: str = f.read()

        self.abs_corsika_path = Path(corsika_path).absolute()
        self.job_pool: list[CorsikaJob] = []
        
        for i in range(n_jobs):
            corsika_copy_dir = self.corsika_tmp_dir / f".corsika_copy_run_{i}"
            self.job_pool.append(CorsikaJob(self.corsika_executable, corsika_copy_dir))

    def wait_for_jobs(self, n_events):
        # show progressbar until close to end
        try:
            with tqdm(total=n_events, unit="shower", unit_scale=True) as pbar:
                while not all([job.is_finished for job in self.jobs]):
                    for job in self.jobs:
                        update = job.poll()
                        pbar.update(update)
                    sleep(0.1)
        except KeyboardInterrupt:
            logging.info("Interrupted by user.")


    def run(self) -> None:
        # create dir if not existent
        self.output.mkdir(parents=True, exist_ok=True)
        
        for idx, (pdgid, n_events) in enumerate(self.primary.items()):
            logging.info(f"Processing primary {Particle.from_pdgid(pdgid).name} ({pdgid})")

            corsikaid = int(Corsika7ID.from_pdgid(pdgid))

            events_per_job = n_events // self.n_jobs
            last_events_per_job = events_per_job + (n_events - events_per_job * n_jobs)

            for i, job in enumerate(self.job_pool[:-1]):
                job.append(
                    self._get_corsika_config(
                        self.n_jobs * idx + i,
                        events_per_job,
                        corsikaid,
                    )
                )
            self.job_pool[-1].start(
                self._get_corsika_config(
                    self.n_jobs * idx + (n_jobs - 1),
                    last_events_per_job,
                    corsikaid,
                )
            )

            wait_for_jobs()

    def _get_corsika_config(
        run_idx: int,
        n_show: int,
        primary_corsikaid: int,
        first_event_idx: int = 1,
    ) -> dir[str, str]:

        return {
            run_idx: f"{run_idx}",
            first_event_idx: f"{first_event_idx}",
            n_show: f"{n_show}",
            dir: str(self.output.absolute()) + "/",
            seed_1: f"{randrange(1, 900_000_000)}",
            seed_2: f"{randrange(1, 900_000_000)}",
            primary: f"{primary_corsikaid}",
            }



