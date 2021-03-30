from dataclasses import dataclass
from enum import Enum

from .service import PusService
from .error_codes import CommonErrorCode


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
    def __init__(self, ident, pus_service_1, tm_distributor):
        super().__init__(5, ident, pus_service_1, tm_distributor)
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
