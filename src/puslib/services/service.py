import queue
import warnings
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable

from puslib.ident import PusIdent
from puslib.packet import PusTcPacket
from puslib.streams.stream import OutputStream

if TYPE_CHECKING:
    from puslib.services.pus_001_request_verification import RequestVerification


class PusServiceType(bytes, Enum):
    description: str  # mypy hint

    def __new__(cls, service_number, description):
        obj = bytes.__new__(cls, [service_number])
        obj._value_ = service_number
        obj.description = description
        return obj

    REQUEST_VERIFICATION = (1, "Request verification")
    DEVICE_ACCESS = (2, "Device access")
    HOUSEKEEPING = (3, "Housekeeping")
    PARAMETER_STATISTICS_REPORTING = (4, "Parameter statistics reporting")
    EVENT_REPORTING = (5, "Event reporting")
    MEMORY_MANAGEMENT = (6, "Memory management")
    FUNCTION_MANAGEMENT = (8, "Function Management")
    TIME_MANAGEMENT = (9, "Time Management")
    TIME_BASED_SCHEDULING = (11, "Time-based scheduling")
    ONBOARD_MONITORING = (12, "On-board monitoring")
    LARGE_PACKET_TRANSFER = (13, "Large packet transfer")
    REALTIME_FORWARDING_CONTROL = (14, "Real-time forwarding control")
    ONBOARD_STORAGE_AND_RETRIEVAL = (15, "On-board storage and retrieval")
    TEST = (17, "Test")
    ONBOARD_CONTROL_PROCEDURES = (18, "On-board control procedures")
    EVENT_ACTION = (19, "Event-action")
    ONBOARD_PARAMETER_MANAGEMENT = (20, "On-board parameter management")
    REQUEST_SEQUENCING = (21, "Request sequencing")
    POSITION_BASED_SCHEDULING = (22, "Position-based scheduling")
    FILE_MANAGEMENT = (23, "File management")

    def __str__(self):
        return self.description


_MAX_STANDARD_SERVICE = 127  # service types 0-127 are reserved for standard PUS services


class PusService:
    """Base class for PUS services."""
    def __init__(self, service_type: PusServiceType | int, ident: PusIdent, pus_service_1: "RequestVerification | None" = None, tm_output_stream: OutputStream | None = None,
                 *, name: str | None = None, description: str | None = None):
        """Create a PUS service instance.

        Arguments:
            service_type -- standard service type, or service type (0-255) of a custom service
            ident -- PUS identifier

        Keyword Arguments:
            pus_service_1 -- PUS service 1 instance (default: {None})
            tm_output_stream -- output stream (default: {None})
            name -- service name, overrides the name of a standard service type (default: {None})
            description -- service description, overrides the description of a standard service type (default: {None})

        Raises:
            ValueError: if the service type is out of range
        """
        if isinstance(service_type, PusServiceType):  # standard service
            self._service_type: PusServiceType | None = service_type
            self._service_number = int(service_type.value)
            self._name = name if name is not None else service_type.name
            self._description = description if description is not None else service_type.description
        else:  # custom service
            if isinstance(service_type, bool) or not isinstance(service_type, int):
                raise TypeError("Service type must be a PusServiceType or an int")
            if not 0 <= service_type <= 255:
                raise ValueError(f"Service type must be in range 0-255, got {service_type}")
            if service_type <= _MAX_STANDARD_SERVICE:
                warnings.warn(f"Service type {service_type} is in the range reserved for standard PUS services (0-{_MAX_STANDARD_SERVICE})", stacklevel=2)
            self._service_type = None
            self._service_number = service_type
            self._name = name if name is not None else f"SERVICE_{service_type}"
            self._description = description if description is not None else ""
        self._subservices: dict[int, Callable[..., Any]] = {}
        self._ident = ident
        self._incoming_tc_queue: queue.SimpleQueue[PusTcPacket] = queue.SimpleQueue()
        self._tm_output_stream = tm_output_stream
        self._pus_service_1 = pus_service_1

    @property
    def service(self) -> int:
        """PUS service type number."""
        return self._service_number

    @property
    def name(self) -> str:
        """Service name."""
        return self._name

    @property
    def description(self) -> str:
        """Service description."""
        return self._description

    def enqueue(self, tc_packet: PusTcPacket):
        """Enqueue an incoming PUS TC packet.

        Arguments:
            tc_packet -- PUS TC packet
        """
        if tc_packet.apid == self._ident.apid and tc_packet.service == self.service and tc_packet.subservice in self._subservices:
            self._incoming_tc_queue.put(tc_packet)

    def process(self):
        """Process queued PUS TC packets.
        """
        while True:
            try:
                tc_packet = self._incoming_tc_queue.get_nowait()
            except queue.Empty:
                break
            subservice_handler = self._subservices[tc_packet.subservice]
            ret = subservice_handler(app_data=tc_packet.app_data)
            if isinstance(ret, bool):
                success = ret
                pus_error_code = None
            elif isinstance(ret, Enum):
                success = False
                pus_error_code = ret
            else:
                raise TypeError("Must return a bool or an enum")

            self._pus_service_1.accept(tc_packet, success=success, failure_code=pus_error_code)
            self._pus_service_1.complete(tc_packet, success=success, failure_code=pus_error_code)

    def update(self) -> None:
        pass

    def _register_sub_service(self, number: int, func: Callable[..., Any]) -> None:
        self._subservices[number] = func
