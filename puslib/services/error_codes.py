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

    PUS3_SID_ALREADY_PRESENT = (30, "Structure ID already exist")
    PUS3_SID_NOT_PRESENT = (31, "Structure ID does not exist")
    PUS3_CANNOT_MODIFY_ENABLED_REPORT = (32, "Report is enabled and cannot be modified")
    PUS3_PARAM_DUPLICATION = (33, "Same parameter is identified more than once in request")

    PUS8_INVALID_FID = (80, "Invalid function ID")
    PUS8_FUNCTION_NOT_IMPLEMENTED = (81, "Function not implemented")
    PUS8_INVALID_ARGS = (82, "Invalid function arguments")
