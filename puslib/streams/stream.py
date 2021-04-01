import abc


class InputStream(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'read') and callable(subclass.read) or NotImplemented)

    @abc.abstractmethod
    def read(self):
        raise NotImplementedError


class OutputStream(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'write') and callable(subclass.write) or NotImplemented)

    @abc.abstractmethod
    def write(self, packet):
        raise NotImplementedError
