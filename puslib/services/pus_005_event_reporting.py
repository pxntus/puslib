import struct
from collections import namedtuple
from functools import partial
from enum import Enum

from .service import PusService, PusServiceType
from puslib import get_pus_policy

_Event = namedtuple('Event', ['severity', 'enabled', 'params_in_report', 'cached_struct', 'trig_func'])


class Severity(Enum):
    INFO = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4


class EventReporting(PusService):
    def __init__(self, ident, pus_service_1, tm_output_stream):
        super().__init__(PusServiceType.EVENT_REPORTING, ident, pus_service_1, tm_output_stream)
        self._register_sub_service(5, self._enable)
        self._register_sub_service(6, self._disable)
        self._events = {}
        self._event_names = {}
        self._eid_param = get_pus_policy().IdType()

    def add(self, eid, name=None, severity=Severity.INFO, enabled=True, params_in_report=None, trig_param=None, to_value=None, from_value=None):
        if eid in self._events:
            raise RuntimeError(f"Event with ID {eid} already exists")
        if name:
            if name in self._event_names:
                raise RuntimeError(f"Event with name '{name}' already exists")
        self._event_names[name] = eid

        fmt = ">" + (self._eid_param.format + "".join([p.format for p in params_in_report])).replace('>', '')
        cached_struct = struct.Struct(fmt)
        event = _Event(severity, enabled, params_in_report, cached_struct, partial(self._trigger, eid, to_value, from_value) if trig_param else None)
        self._events[eid] = event
        if event.trig_func:
            trig_param.subscribe(event.trig_func)

    def dispatch(self, eid_or_name):
        if isinstance(eid_or_name, int):
            if eid_or_name not in self._events:
                raise RuntimeError(f"Event with ID {eid_or_name} does not exist")
        elif isinstance(eid_or_name, str):
            if eid_or_name not in self._event_names:
                raise RuntimeError(f"Event with name {eid_or_name} does not exist")
            eid_or_name = self._event_names[eid_or_name]
        else:
            raise RuntimeError(f"Unknonw event identifier: {eid_or_name}")
        event = self._events[eid_or_name]

        time = get_pus_policy().CucTime()
        self._eid_param.value = eid_or_name
        values = [self._eid_param.value] + [p.value for p in event.params_in_report]
        payload = event.cached_struct.pack(*values)
        report = get_pus_policy().PusTmPacket(
            apid=self._ident.apid,
            seq_count=self._ident.seq_count(),
            service_type=self._service_type.value,
            service_subtype=event.severity.value,
            time=time,
            payload=payload
        )
        self._tm_output_stream.write(report)

    def _trigger(self, eid, to_value=None, from_value=None, old_value=None, new_value=None):
        if not to_value and not from_value:  # if trig parameter has changed
            self.dispatch(eid)
        elif not from_value:  # if trig parameter has changed to 'to_value'
            if to_value == new_value:
                self.dispatch(eid)
        else:  # if trig parameter has changed from 'from_value' to 'to_value'
            if from_value == old_value and to_value == new_value:
                self.dispatch(eid)

    def _enable(self, app_data):
        return True

    def _disable(self, app_data):
        return True
