
class PusException(Exception):
    pass


class CrcException(PusException):
    pass


class IncompletePacketException(PusException):
    pass


class InvalidPacketException(PusException):
    pass


class TooSmallBufferException(PusException):
    pass


class InvalidTimeFormat(PusException):
    pass


class TcPacketRoutingError(PusException):
    pass
