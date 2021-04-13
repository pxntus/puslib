from enum import IntEnum

from . import services
from .ident import PusIdent
from .exceptions import TcPacketRoutingError
from .services.service import PusServiceType


def periodic(scheduler, interval, priority, action, actionargs=()):
    scheduler.enter(interval, priority, periodic, (scheduler, interval, priority, action, actionargs))
    action(*actionargs)


class Priority(IntEnum):
    HIGH = 1
    NORMAL = 2
    LOW = 3


class Process:
    def __init__(self, apid, tm_output_stream, scheduler, housekeeping=False, event_reporting=False, function_management=False, test=False):

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
    def apid(self):
        return self._ident.apid

    def addparam(self, param_id, param):
        self._params[param_id] = param

    def forward(self, tc_packet):
        if tc_packet.apid != self.apid:
            raise TcPacketRoutingError()
        if tc_packet.service not in self._pus_services:
            raise TcPacketRoutingError(f"No PUS service {tc_packet.service} in application process (APID {tc_packet.apid})")
        self._pus_services[tc_packet.service].enqueue(tc_packet)
        self._pus_services[tc_packet.service].process()

    def action(self, interval, priority=Priority.NORMAL):
        def add_action(func):
            self._actions[func.__name__] = func
            periodic(self._scheduler, interval, priority, func)
        return add_action

    def function(self, fid, args):
        def add_function(func):
            if PusServiceType.FUNCTION_MANAGEMENT.value not in self._pus_services:
                raise RuntimeError("Process has no function management service")
            self._pus_service_8.add(func, fid, args)
        return add_function
