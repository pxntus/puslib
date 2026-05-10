import abc


class InputStream(metaclass=abc.ABCMeta):
    """Abstract base class for TM packet input streams."""

    @classmethod
    def __subclasshook__(cls, subclass):
        return hasattr(subclass, 'read') and callable(subclass.read) or NotImplemented

    @abc.abstractmethod
    def read(self):
        """Read and return a single TM packet."""
        raise NotImplementedError


class OutputStream(metaclass=abc.ABCMeta):
    """Abstract base class for TM packet output streams."""

    @classmethod
    def __subclasshook__(cls, subclass):
        return hasattr(subclass, 'write') and callable(subclass.write) or NotImplemented

    @abc.abstractmethod
    def write(self, packet):
        """Write a TM packet to the stream.

        Arguments:
            packet -- TM packet to write
        """
        raise NotImplementedError
