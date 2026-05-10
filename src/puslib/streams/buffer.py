from queue import SimpleQueue
from typing import Any

from puslib.streams.stream import OutputStream


class QueuedOutput(OutputStream):
    """In-memory queue-backed output stream. Useful for testing and inter-thread buffering."""

    def __init__(self):
        self._queue: SimpleQueue[Any] = SimpleQueue()

    @property
    def size(self) -> int:
        """Number of packets currently in the queue."""
        return self._queue.qsize()

    def write(self, packet: Any) -> None:
        """Enqueue a packet.

        Arguments:
            packet -- TM packet to enqueue
        """
        self._queue.put(packet)

    def empty(self) -> bool:
        """Return True if the queue contains no packets."""
        return self._queue.empty()

    def get(self) -> Any | None:
        """Remove and return the next packet, or None if the queue is empty."""
        if self.empty():
            return None
        return self._queue.get()
