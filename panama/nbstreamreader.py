# Adapted from http://eyalarubas.com/python-subproc-nonblock.html
from threading import Thread
from queue import Queue, Empty
from time import sleep


class NonBlockingStreamReader:
    def __init__(self, stream):
        """
        stream: the stream to read from.
                Usually a process' stdout or stderr.
        """

        self._s = stream
        self._q = Queue()

        self._is_alive = True

        def _populateQueue(stream, queue, is_alive, wait):
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

        self._t = Thread(
            target=_populateQueue, args=(self._s, self._q, self._is_alive, self._wait)
        )
        self._t.daemon = True
        self._t.start()  # start collecting lines from the stream

    def __del__(self):
        self._is_alive = False
        self._t.join(timeout=self._wait * 2)
        if self._t.is_alive():
            raise RuntimeError("Could not kill thread in NonBlockingStreamReader")

    def readline(self, timeout=None):
        try:
            return self._q.get(block=timeout is not None, timeout=timeout)
        except Empty:
            return None
