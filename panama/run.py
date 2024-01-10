"""
Classes handling the parallel execution of CORSIKA7 processes.
"""
from __future__ import annotations

import io
import logging
import shutil
from contextlib import suppress
from os import symlink
from pathlib import Path
from random import randrange
from random import seed as set_seed
from subprocess import PIPE, Popen, TimeoutExpired
from time import sleep
from types import TracebackType

from particle import Corsika7ID, Particle
from tqdm import tqdm

from ._nbstreamreader import NonBlockingStreamReader as NBSR

CORSIKA_FILE_ERROR = "STOP FILOPN: FATAL PROBLEM OPENING FILE"
CORSIKA_EVENT_FINISHED = b"PRIMARY PARAMETERS AT FIRST INTERACTION POINT AT HEIGHT"
CORSIKA_RUN_END = b"END OF RUN"

logger = logging.getLogger("panama")


class CorsikaJob:
    """
    This class handles the execution and monitoring of one single CORSIKA7 process.
    Usually, there should be no need to use this class directly, use CorsikaRunner instead.
    """

    def __init__(
        self, corsika_executable: Path, corsika_copy_dir: Path, card_template: str
    ) -> None:
        """

        Parameters
        ----------
        corsika_executable : Path
           Path of the CORSIKA7 executable.
        corsika_copy_dir : Path
            The path to where the original executable will be symlinked,
            so it can be run multiple times in parallel.
            CORSIKA7 for some reason does not allow running the same executable
            multiple times.
        card_template : str
            The string containing a valid CORSIKA7 run card with additional
            python-like templates (e.g. `{emin}`).
            The template will be formatted when calling start.

        """
        self.corsika_copy_dir = corsika_copy_dir
        self.corsika_copy_dir.mkdir(parents=True, exist_ok=False)
        self.card_template = card_template

        # symlink all files in the corsika run dir
        for p in corsika_executable.absolute().parent.glob("*"):
            if not p.is_file():
                continue
            symlink(str(p.absolute()), str((corsika_copy_dir / p.name).absolute()))
        self.this_corsika_path = self.corsika_copy_dir / corsika_executable.name

        self.running: None | Popen[bytes] = None
        self.config: None | dict[str, str] = None
        self.stream: None | NBSR = None
        self.n_showers = 0
        self.finished_showers = 0
        self.output = b""
        self.save_std_file: None | io.TextIOWrapper = None

    def clean(self) -> None:
        """
        Cleans the temporary directory.
        """
        shutil.rmtree(self.corsika_copy_dir, ignore_errors=True)

    @property
    def is_finished(self) -> bool:
        """
        Returns True if the process is not running, False otherwise
        """
        return self.running is None

    def start(
        self, corsika_config: dict[str, str], save_std: Path | None = None
    ) -> None:
        """
        Starts the CORSIKA7 process with the given parameters, if it is not
        already running.

        Parameters
        ----------
        corsika_config : dict[str, str]
            The template values which will be filled in the template corsika card.
        save_std : Path | None, optional
            If provided, the std output of CORSIKA7 will be saved to this path.

        Raises
        ------
        RuntimeError
            If the process is already running.

        """
        if self.running is not None:
            raise RuntimeError("Can't use this CorsikaJob, it's still running!")

        self.n_showers = int(corsika_config["n_show"])
        self.finished_showers = 0
        self.running = Popen(
            self.this_corsika_path.absolute(),
            stdin=PIPE,
            stdout=PIPE,
            cwd=self.this_corsika_path.absolute().parent,
        )

        self.config = corsika_config

        assert self.save_std_file is None

        # TODO: This is not really nice...
        # I don't see how context handlers can be easily used here
        if save_std is not None:
            self.save_std_file = open(save_std, "w")  # noqa: SIM115

        # this is what is expected...
        # Feels like a hack...
        with suppress(TimeoutExpired):
            stdin, stdout = self.running.communicate(
                input=self.card_template.format(**corsika_config).encode("ASCII"),
                timeout=1,
            )

            # this code is only reachable when corsika takes less then 1 second to run, which
            # is very unlikely and hard to test, thus we do not consider these
            # lines for coverage
            if self.save_std_file is not None:  # pragma: no cover
                self.save_std_file.write(stdout.decode("ASCII"))

        assert self.running.stdout is not None
        self.stream = NBSR(self.running.stdout)

    def poll(self) -> int | None:
        """
        Returns how many showers finished since last poll or None if the process is finished.

        Returns
        -------
        n_update: The number of showers finished since last poll or None if process is finished
        """
        if self.running is None:
            return None

        if (return_code := self.running.poll()) is not None:
            if return_code != 0:
                logger.error(
                    f"Return code of corsika is {return_code}. This indicates a failed run."
                )

            return self.join()

        finished = 0

        assert self.stream is not None

        line = self.stream.readline()
        if line is not None:
            self.output = b""
        while line is not None:
            logger.debug(line.decode("ASCII"))
            logger.debug(f"finished events = {line.count(CORSIKA_EVENT_FINISHED)}")
            finished += line.count(CORSIKA_EVENT_FINISHED)
            self.output += line

            if self.save_std_file is not None:
                self.save_std_file.write(line.decode("ASCII"))

            line = self.stream.readline()

        self.finished_showers += finished

        return finished

    def join(self) -> int:
        """
        Waits for the CORSIKA7 process to finish, if it is running.

        Returns
        -------
        n_update: The number of finished events in the last output.

        Raises
        ------
        RuntimeError
            If the process is already finished.
        """
        if self.running is None:
            raise RuntimeError("Job is already finished")
        assert self.stream is not None

        (last_stdout, last_stderr_data) = self.running.communicate()
        line = self.stream.readline()

        finished = 0

        while line is not None:
            finished += line.count(CORSIKA_EVENT_FINISHED)
            self.output += line
            if self.save_std_file is not None:
                self.save_std_file.write(line.decode("ASCII"))
            line = self.stream.readline()

        finished += last_stdout.count(CORSIKA_EVENT_FINISHED)
        self.output += last_stdout
        logger.debug(f"{self.output.decode('ASCII')}")

        if self.save_std_file is not None:
            self.save_std_file.write(last_stdout.decode("ASCII"))

        # this is really hard to test, since corsika must crash, not only
        # encounter e.g. bad input
        if CORSIKA_RUN_END not in self.output:  # pragma: no cover
            logger.warning(
                f"Corsika Output:\n {self.output.decode('ASCII')} \n'END OF RUN' not in corsika output. May indicate failed run. See the output above."
            )

        self._reset()

        return finished

    def _reset(self) -> None:
        self.running = None
        self.config = None
        self.stream = None
        self.finished_showers = 0
        if self.save_std_file is not None:
            self.save_std_file.close()
            self.save_std_file = None


class CorsikaRunner:
    """
    This class manages running multiple CORSIKA7 processes in parallel, by splitting
    up the requested showers in badges and changing the initial seeds for CORSIKA7 for
    each batch.
    It also provides a progressbar by investigating the stdout from CORSIKA7.
    To automatically clean up temporary directories, this class can be used in a
    `with`-statement. Otherwise, call `corsika_runner.clean()` to delete the tmp dirs.
    """

    def __init__(
        self,
        primary: dict[int, int],
        n_jobs: int,
        template_path: Path,
        output: Path,
        corsika_executable: Path,
        corsika_tmp_dir: Path,
        seed: None | int = None,
        save_std: bool = False,
        first_run_number: int = 0,
        first_event_number: int = 1,
    ) -> None:
        """
        This class manages running multiple CORSIKA7 processes in parallel, by splitting
        up the requested showers in badges and changing the initial seeds for CORSIKA7 for
        each batch.
        It also provides a progressbar by investigating the stdout from CORSIKA7.
        This means that "parallelization" is handled by the operating system. If you are only
        allowed to use one core, this will not parallelize anything.

        Parameters
        ----------
        primary : dict[int, int]
            Mapping from PDGID to number of events with this primary.
            10 Proton and 20 Helium-4 air showers would mean `{2212: 10, 1000020040: 20}`.
            (Use the proton pdgid, not the Hydrogen-1 pdgid!)
            Conversion between pdgid and Corsika7ID is handled by the particle python package.
            All primaries of one type are processed parallel, and the different
            primaries are processed after each other.
            This guarantees, that each progress running parallel at a time
            will approximately run an equal amount of time.

        n_jobs : int
            The number of parallel jobs to send to the operating system.

        template_path : Path
            The path to the template of the CORISKA7 card.

        output : Path
            The path where the CORSIKA7 process will produce the output.

        corsika_executable : Path
            The path to the CORSIKA7 executable.

        corsika_tmp_dir : Path
            A temporary directory to symlink the CORSIKA7 executable to.
            Since CORSIKA7 can not be run in parallel from the same executable
            directly.
            The copied/symlinked files will be deleted automatically when used
            in a context manager (`with`-statement), otherwise you have to call
            the `clean()` method.
            The directory itself will not be deleted, only the used subdir in the
            directory.

        seed : None | int, optional
            The seed to use for generating the seeds for the CORSIKA7 program.
            If None is given, entropic source of the computer will be used.

        save_std : bool, optional
            Whether or not to save the standard output of the CORSIKA7 programs.
            If true, the output is available as "prim{pdgid}_job{jobid}.log" in the
            output folder.

        first_run_number : int = 0, optional
            The run number the first run will get.
            All following runs will increment the run number by one.

        first_event_number : int = 1, optional
            The event number the first event in each run will get.

        Raises
        ------
        ValueError
            If the input is not consistent.

        """
        self.primary = primary
        self.n_jobs = n_jobs
        self.output = Path(output)
        if self.output.exists():
            logger.warning(
                f"Output Directory ({self.output.absolute()}) already exists. CORSIKA7 will crash if an output file already exists. Consider removing the directory before running the simulation."
            )

        self.corsika_executable = Path(corsika_executable)
        self.corsika_tmp_dir = Path(corsika_tmp_dir)
        self.save_std = save_std
        self.first_run_number = first_run_number
        self.first_event_number = first_event_number

        # we always need at least n_showers if we want to run n_jobs
        if not all(n_jobs <= n_showers for n_showers in primary.values()):
            raise ValueError(
                "n_jobs must be smaller or equal to the number of showers (for every primary)"
            )

        if seed is not None:
            set_seed(seed)
        self.seed = seed

        with open(template_path) as f:
            self.card_template: str = f.read()

        self.job_pool: list[CorsikaJob] = []

        for i in range(self.n_jobs):
            corsika_copy_dir = self.corsika_tmp_dir / f".corsika_copy_run_{i}"
            self.job_pool.append(
                CorsikaJob(
                    self.corsika_executable, corsika_copy_dir, self.card_template
                )
            )

    def _wait_for_jobs(self, disable_pb: bool = False) -> None:
        """
        Wait until all jobs are finished. This is called automatically  by run at the moment.


        Parameters
        ----------
        disable_pb : bool
            If True, disables the progressbar.

        """
        n_events = sum([job.n_showers for job in self.job_pool])
        # show progressbar until close to end
        try:
            with tqdm(
                total=n_events, unit="shower", unit_scale=True, disable=disable_pb
            ) as pbar:
                while not all(job.is_finished for job in self.job_pool):
                    for job in self.job_pool:
                        update = job.poll()
                        if update is not None:
                            pbar.update(update)
                    sleep(0.1)
        # testing keyboard interrupt is hard
        except KeyboardInterrupt:  # pragma: no cover
            logger.info("Interrupted by user.")

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.clean()

    def __enter__(self) -> CorsikaRunner:
        return self

    def __del__(self) -> None:
        self.clean()

    def clean(self) -> None:
        """
        Deletes the temporary directories, this is called when the object is deleted.
        This method has to be called, before a different CorsikaRunner with the
        same tmp_dir can be constructed.
        The object can't be used anymore after calling this method.
        """
        for job in self.job_pool:
            job.clean()

    def run(self, disable_pb: bool = False) -> None:
        """
        Start all the processes and wait for them to finish.
        Each primary element is run after another.

        Parameters
        ----------
        disable_pb : bool
            If True, disables the (tqdm) progressbar.

        """
        # create dir if not existent
        self.output.mkdir(parents=True, exist_ok=True)

        for idx, (pdgid, n_events) in enumerate(self.primary.items()):
            logger.info("#" * 50)
            logger.info(
                f"Running primary '{Particle.from_pdgid(pdgid).name}' (pdgid: {pdgid})"
            )

            corsikaid = int(Corsika7ID.from_pdgid(pdgid))

            events_per_job = n_events // self.n_jobs
            last_events_per_job = events_per_job + (
                n_events - events_per_job * self.n_jobs
            )

            for i, job in enumerate(self.job_pool[:-1]):
                if self.save_std:
                    save_std_path = self.output.absolute() / f"prim{pdgid}_job{i}.log"
                else:
                    save_std_path = None
                job.start(
                    self._get_corsika_config(
                        self.n_jobs * idx + i,
                        events_per_job,
                        corsikaid,
                    ),
                    save_std_path,
                )

            if self.save_std:
                save_std_path = (
                    self.output.absolute()
                    / f"prim{pdgid}_job{len(self.job_pool)-1}.log"
                )
            else:
                save_std_path = None
            self.job_pool[-1].start(
                self._get_corsika_config(
                    self.n_jobs * idx + (self.n_jobs - 1),
                    last_events_per_job,
                    corsikaid,
                ),
                save_std_path,
            )

            self._wait_for_jobs(disable_pb)

    def _get_corsika_config(
        self,
        run_idx: int,
        n_show: int,
        primary_corsikaid: int,
    ) -> dict[str, str]:
        return {
            "run_idx": f"{run_idx+self.first_run_number}",
            "first_event_idx": f"{self.first_event_number}",
            "n_show": f"{n_show}",
            "dir": str(self.output.absolute()) + "/",
            "seed_1": f"{randrange(1, 900_000_000)}",
            "seed_2": f"{randrange(1, 900_000_000)}",
            "primary": f"{primary_corsikaid}",
        }
