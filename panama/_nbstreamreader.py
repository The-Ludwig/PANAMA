"""
A non-blocking stream reader used to read output from
multiple running CORSIKA instances.
Only to be used internally.
Adapted from http://eyalarubas.com/python-subproc-nonblock.html
"""
from __future__ import annotations

from queue import Empty, Queue
from threading import Thread
from typing import IO, Any


class NonBlockingStreamReader:
    def __init__(self, stream: IO[Any], wait: int = 5) -> None:
        """
        stream: the stream to read from.
                Usually a process' stdout or stderr.
        """

        self._s = stream
        self._q: Queue[bytes] = Queue()
        self._wait = wait

        self._is_alive = True

        def _populateQueue(
            stream: IO[Any], queue: Queue[bytes], is_alive: bool
        ) -> None:
            """
            Collect lines from 'stream' and put them in 'quque'.
            """

            while is_alive:
                line = stream.readline()
                while line:
                    queue.put(line)
                    line = stream.readline()
                # we arrive here if line is None, this means that the stream is closed
                return

        self._t = Thread(target=_populateQueue, args=(self._s, self._q, self._is_alive))
        self._t.daemon = True
        self._t.start()  # start collecting lines from the stream

    def __del__(self) -> None:
        self._is_alive = False
        self._t.join(timeout=self._wait)
        if self._t.is_alive():  # pragma: no cover
            raise RuntimeError("Could not kill thread in NonBlockingStreamReader")

    def readline(self, timeout: int | None = None) -> bytes | None:
        try:
            return self._q.get(block=timeout is not None, timeout=timeout)
        except Empty:
            return None
