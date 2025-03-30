import sched
from enum import IntEnum
from typing import Sequence, Callable

from puslib import services
from puslib.services.service import PusServiceType
from puslib.ident import PusIdent
from puslib.exceptions import TcPacketRoutingError
from puslib.streams.stream import OutputStream
from puslib.parameter import Parameter
from puslib.packet import PusTcPacket


def periodic(scheduler: sched.scheduler, interval: int, priority: int, action, actionargs=()):
    scheduler.enter(interval, priority, periodic, (scheduler, interval, priority, action, actionargs))
    action(*actionargs)


class Priority(IntEnum):
    HIGH = 1
    NORMAL = 2
    LOW = 3


class Process:
    """Represents an application process as defined by the PUS standard.

    According to the PUS standard an application process is an "element of
    the space system that can host one or more subservice entities".
    """
    def __init__(self, apid: int, tm_output_stream: OutputStream, scheduler: sched.scheduler,
                 housekeeping: bool = False, event_reporting: bool = False, function_management: bool = False, test: bool = False):
        """Create an application process.

        Arguments:
            apid -- application ID
            tm_output_stream -- TM output stream
            scheduler -- scheduler object

        Keyword Arguments:
            housekeeping -- enable housekeeping service (default: {False})
            event_reporting -- enable event reporting service (default: {False})
            function_management -- enable function management service (default: {False})
            test -- enable test service (default: {False})
        """
        self._ident = PusIdent(apid)
        self._tm_output_stream = tm_output_stream
        self._scheduler = scheduler

        self._params = {}

        self._pus_services = {}
        self._pus_service_1 = services.RequestVerification(self._ident, tm_output_stream)
        self._pus_services[1] = self._pus_service_1
        if housekeeping:
            self._pus_service_3 = services.Housekeeping(self._ident, self._pus_service_1, tm_output_stream)
            self._pus_services[3] = self._pus_service_3
        if event_reporting:
            self._pus_service_5 = services.EventReporting(self._ident, self._pus_service_1, tm_output_stream)
            self._pus_services[5] = self._pus_service_5
        if function_management:
            self._pus_service_8 = services.FunctionManagement(self._ident, self._pus_service_1)
            self._pus_services[8] = self._pus_service_8
        if test:
            self._pus_service_17 = services.Test(self._ident, self._pus_service_1, tm_output_stream)
            self._pus_services[17] = self._pus_service_17

        self._actions = {}

    @property
    def apid(self) -> int:
        return self._ident.apid

    def addparam(self, param_id: int, param: Parameter):
        """Add parameter to application service.

        Arguments:
            param_id -- parameter ID (PID)
            param -- parameter
        """
        self._params[param_id] = param

    def forward(self, tc_packet: PusTcPacket):
        """Forward TC packet to application service.

        Arguments:
            tc_packet -- PUS TC packet
        """
        if tc_packet.apid != self.apid:
            raise TcPacketRoutingError()
        if tc_packet.service not in self._pus_services:
            raise TcPacketRoutingError(f"No PUS service {tc_packet.service} in application process (APID {tc_packet.apid})")
        self._pus_services[tc_packet.service].enqueue(tc_packet)
        self._pus_services[tc_packet.service].process()

    def action(self, interval: int | float, priority=Priority.NORMAL):
        """Add an action to be executed with some interval.

        Arguments:
            interval -- interval in seconds

        Keyword Arguments:
            priority -- priority of action (default: {Priority.NORMAL})
        """
        def add_action(func):
            self._actions[func.__name__] = func
            periodic(self._scheduler, interval, priority, func)
        return add_action

    def function(self, fid: int, args: Sequence[Parameter]) -> Callable[...]:
        """Add a function to the function management service.

        Arguments:
            fid -- function ID
            args -- arguments to the functions
        """
        def add_function(func):
            if PusServiceType.FUNCTION_MANAGEMENT.value not in self._pus_services:
                raise RuntimeError("Process has no function management service")
            self._pus_service_8.add(func, fid, args)
        return add_function
