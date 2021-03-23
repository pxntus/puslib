from enum import Enum

from .pus_001_request_verification import RequestVerification
from .pus_017_test import Test


class PusServiceType(bytes, Enum):
    def __new__(cls, service_number, description, service_class):
        obj = bytes.__new__(cls, [service_number])
        obj._value_ = service_number
        obj.description = description
        obj.make = service_class
        return obj

    REQUEST_VERIFICATION = (1, "Request verification", RequestVerification)
    DEVICE_ACCESS = (2, "Device access", None)
    HOUSEKEEPING = (3, "Housekeeping", None)
    PARAMETER_STATISTICS_REPORTING = (4, "Parameter statistics reporting", None)
    EVENT_REPORTING = (5, "Event reporting", None)
    MEMORY_MANAGEMENT = (6, "Memory management", None)
    FUNCTION_MANAGEMENT = (8, "Function Management", None)
    TIME_MANAGEMENT = (9, "Time Management", None)
    TIME_BASED_SCHEDULING = (11, "Time-based scheduling", None)
    ONBOARD_MONITORING = (12, "On-board monitoring", None)
    LARGE_PACKET_TRANSFER = (13, "Large packet transfer", None)
    REALTIME_FORWARDING_CONTROL = (14, "Real-time forwarding control", None)
    ONBOARD_STORAGE_AND_RETRIEVAL = (15, "On-board storage and retrieval", None)
    TEST = (17, "Test", Test)
    ONBOARD_CONTROL_PROCEDURES = (18, "On-board control procedures", None)
    EVENT_ACTION = (19, "Event-action", None)
    ONBOARD_PARAMETER_MANAGEMENT = (20, "On-board parameter management", None)
    REQUEST_SEQUENCING = (21, "Request sequencing", None)
    POSITION_BASED_SCHEDULING = (22, "Position-based scheduling", None)
    FILE_MANAGEMENT = (23, "File management", None)

    def __str__(self):
        return self.description
