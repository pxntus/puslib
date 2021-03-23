from enum import Enum


class CommonErrorCode(bytes, Enum):
    def __new__(cls, value, description):
        obj = bytes.__new__(cls, [value])
        obj._value_ = value
        obj.description = description
        return obj

    ILLEGAL_APID = (0, "Illegal APID")
    INCOMPLETE = (1, "Incomplete or invalid length packet")
    INCORRECT_CHECKSUM = (2, "Incorrect checksum")
    ILLEGAL_PACKET_TYPE = (3, "Illegal packet type")
    ILLEGAL_PACKET_SUBTYPE = (4, "Illegal packet subtype")
    ILLEGAL_APP_DATA = (5, "Illegal or inconsistent application data")
