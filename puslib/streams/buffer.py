from queue import SimpleQueue

from .stream import OutputStream


class QueuedOutput(OutputStream):
    def __init__(self):
        self._queue = SimpleQueue()

    @property
    def size(self):
        return self._queue.qsize()

    def write(self, packet):
        self._queue.put(packet)

    def empty(self):
        return self._queue.empty()

    def get(self):
        if self.empty():
            return None
        return self._queue.get()
