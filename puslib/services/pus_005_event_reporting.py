from dataclasses import dataclass
from enum import Enum

from .service import PusService, PusServiceType


class Severity(Enum):
    INFO = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4


@dataclass
class Report:
    enabled: bool = False
    trig = None
    severity: Severity = Severity.INFO
    params: list = None


class EventReporting(PusService):
    def __init__(self, ident, pus_service_1, tm_output_stream):
        super().__init__(PusServiceType.EVENT_REPORTING, ident, pus_service_1, tm_output_stream)
        self._register_sub_service(5, self._enable)
        self._reports = {}

    def event(self, func, rid, report):
        report.trig = func
        self._reports[rid] = report

        def wrapper(*args, **kwargs):
            #func(*args, **kwargs)
            pass

        return wrapper

    def _enable(self, app_data):
        return True
