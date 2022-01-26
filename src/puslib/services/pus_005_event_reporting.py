import struct
from functools import partial
from enum import IntEnum

from .service import PusService, PusServiceType
from .param_report import ParamReport
from .. import get_pus_policy


class Severity(IntEnum):
    INFO = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4


class Report(ParamReport):
    def __init__(self, eid, severity, enabled=True, params_in_report=None):
        super().__init__(eid, enabled, params_in_report)
        self._severity = severity

    @property
    def severity(self):
        return self._severity


class EventReporting(PusService):
    def __init__(self, ident, pus_service_1, tm_output_stream):
        super().__init__(PusServiceType.EVENT_REPORTING, ident, pus_service_1, tm_output_stream)
        self._register_sub_service(5, partial(self._toggle, enable=True))
        self._register_sub_service(6, partial(self._toggle, enable=False))
        self._register_sub_service(7, self._report_disabled_events)
        self._reports = {}

    def add(self, eid, severity=Severity.INFO, params_in_report=None, enabled=True, trig_param=None, to_value=None, from_value=None):
        if eid in self._reports:
            raise RuntimeError(f"Event with ID {eid} already exists")

        report = Report(eid, severity, enabled, params_in_report)
        self._reports[eid] = report
        if trig_param:
            trig_param.subscribe(partial(self._trigger, report, to_value, from_value))
        return report

    def dispatch(self, eid_or_report):
        if isinstance(eid_or_report, int):
            if eid_or_report not in self._reports:
                raise RuntimeError(f"Event with ID {eid_or_report} does not exist")
            report = self._reports[eid_or_report]
        elif isinstance(eid_or_report, Report):
            report = eid_or_report
        else:
            raise RuntimeError("Unknonw report identifier")
        if not report.enabled:
            return

        time = get_pus_policy().CucTime()
        payload = report.to_bytes()
        packet = get_pus_policy().PusTmPacket(
            apid=self._ident.apid,
            seq_count=self._ident.seq_count(),
            service_type=self._service_type.value,
            service_subtype=report.severity,
            time=time,
            data=payload
        )
        self._tm_output_stream.write(packet)

    def _trigger(self, report, to_value=None, from_value=None, old_value=None, new_value=None):
        if not report.enabled:
            return
        if not to_value and not from_value:  # if trig parameter has changed
            self.dispatch(report)
        elif not from_value:  # if trig parameter has changed to 'to_value'
            if to_value == new_value:
                self.dispatch(report)
        else:  # if trig parameter has changed from 'from_value' to 'to_value'
            if from_value == old_value and to_value == new_value:
                self.dispatch(report)

    def _toggle(self, app_data, enable=True):
        try:
            num_ids = get_pus_policy().event_reporting.count_type(
                get_pus_policy().event_reporting.count_type.from_bytes(app_data)
            )
            fmt = '>' + f"{num_ids.value}{get_pus_policy().event_reporting.event_definition_id_type().format}".replace('>', '')
            ids = struct.unpack(fmt, app_data[num_ids.size:])
        except struct.error:
            return False
        if not all(eid in self._reports for eid in ids):
            return False
        for eid in ids:
            if eid in self._reports:
                if enable:
                    self._reports[eid].enable()
                else:
                    self._reports[eid].disable()
        return True

    def _report_disabled_events(self, app_data):
        if app_data is not None:
            return False
        time = get_pus_policy().CucTime()
        disabled_ids = [report.id for eid, report in self._reports.items() if not report.enabled]
        num_ids = get_pus_policy().event_reporting.count_type(len(disabled_ids))
        fmt = ">" + f"{num_ids.format}{num_ids.value}{get_pus_policy().event_reporting.event_definition_id_type().format}".replace('>', '')
        payload = struct.pack(fmt, num_ids.value, *disabled_ids)
        packet = get_pus_policy().PusTmPacket(
            apid=self._ident.apid,
            seq_count=self._ident.seq_count(),
            service_type=self._service_type.value,
            service_subtype=8,
            time=time,
            data=payload
        )
        self._tm_output_stream.write(packet)
        return True
