import struct
from functools import partial

from .service import PusService, PusServiceType
from .param_report import ParamReport
from .error_codes import CommonErrorCode
from puslib import get_pus_policy


class Report(ParamReport):
    def __init__(self, sid, collection_interval, enabled=True, params_in_report=None):
        super().__init__(sid, enabled, params_in_report)
        self._collection_interval = collection_interval

    @property
    def collection_interval(self):
        return self._collection_interval


class Housekeeping(PusService):
    def __init__(self, ident, pus_service_1, tm_output_stream, params):
        super().__init__(PusServiceType.HOUSEKEEPING, ident, pus_service_1, tm_output_stream)
        self._params = params
        self._housekeeping_reports = {}
        self._diagnostic_reports = {}
        self._register_sub_service(1, partial(self._create_report, diagnostic=False))
        self._register_sub_service(2, partial(self._create_report, diagnostic=True))
        self._register_sub_service(3, partial(self._delete_reports, diagnostic=False))
        self._register_sub_service(4, partial(self._delete_reports, diagnostic=True))
        self._register_sub_service(5, partial(self._toggle_reports, diagnostic=False, enable=True))
        self._register_sub_service(6, partial(self._toggle_reports, diagnostic=False, enable=False))
        self._register_sub_service(7, partial(self._toggle_reports, diagnostic=True, enable=True))
        self._register_sub_service(8, partial(self._toggle_reports, diagnostic=True, enable=False))
        self._register_sub_service(9, partial(self._request_report_structures, diagnostic=False))
        self._register_sub_service(11, partial(self._request_report_structures, diagnostic=True))
        self._register_sub_service(27, partial(self._request_reports, diagnostic=False))
        self._register_sub_service(28, partial(self._request_reports, diagnostic=True))
        self._register_sub_service(29, partial(self._append_report, diagnostic=False))
        self._register_sub_service(30, partial(self._append_report, diagnostic=True))
        self._register_sub_service(31, partial(self._modify_report_intervals, diagnostic=False))
        self._register_sub_service(32, partial(self._modify_report_intervals, diagnostic=True))
        self._register_sub_service(33, partial(self._request_interval_properties, diagnostic=False))
        self._register_sub_service(34, partial(self._request_interval_properties, diagnostic=True))

    def add(self, sid, collection_interval, params_in_report=None, enabled=True, diagnostic=False):
        reports = self._diagnostic_reports if diagnostic else self._housekeeping_reports
        if sid in reports:
            raise RuntimeError(f"Report with ID {sid} already exists")

        report = Report(sid, collection_interval, enabled, params_in_report)
        reports[sid] = report
        return report

    def _create_report(self, app_data, diagnostic=False):
        reports = self._diagnostic_reports if diagnostic else self._housekeeping_reports

        try:
            sid = get_pus_policy().housekeeping.structure_id_type()
            sid.value = sid.from_bytes(app_data)
            if sid.value in reports:
                return CommonErrorCode.PUS3_SID_ALREADY_PRESENT  # ECSS-E-ST-70-41C, 6.3.3.5.1.d.1
            offset = sid.size

            collection_interval = get_pus_policy().housekeeping.collection_interval_type()
            collection_interval.value = collection_interval.from_bytes(app_data[offset:])
            offset += collection_interval.size

            # parse number of parameters in the report definition
            n1 = get_pus_policy().housekeeping.count_type()
            n1.value = n1.from_bytes(app_data[offset:])
            offset += n1.size

            # parse parameter IDs
            param_id_dummy = get_pus_policy().common.param_id_type()
            fmt = ">" + f"{n1.value}{param_id_dummy.format}".replace('>', '')
            test = len(app_data)
            param_ids = struct.unpack(fmt, app_data[offset:offset + struct.calcsize(fmt)])
            if len(param_ids) != len(set(param_ids)):
                return CommonErrorCode.PUS3_PARAM_DUPLICATION  # ECSS-E-ST-70-41C, 6.3.3.5.1.d.2
            param_ids = [param_id for param_id in param_ids if param_id in self._params]
            offset += struct.calcsize(fmt)

            # parse number of fixed-length arrays
            nfa = get_pus_policy().housekeeping.count_type()
            nfa.value = nfa.from_bytes(app_data[offset:])
            if nfa.value != 0:
                raise NotImplementedError  # super commutated parameters is not supported

            params = [self._params[param_id] for param_id in param_ids]
            reports[sid.value] = Report(sid=sid.value, collection_interval=collection_interval.value, enabled=False, params_in_report=params)
            return True

        except struct.error as e:
            return CommonErrorCode.INCOMPLETE

    def _for_each_report_id(self, app_data, diagnostic, operation, *argv):
        """Help function to simplify handling of requests with N report IDs.

        The request, or command, should have the following structure:

            +-------+---------------+-----------------+---------+---------------+
            |   N   | Report ID [N] | Report ID [N-1] |   ...   | Report ID [1] |
            +-------+---------------+-----------------+---------+---------------+

        where N is the number of report IDs in the request.
        """
        reports = self._diagnostic_reports if diagnostic else self._housekeeping_reports
        try:
            # parse number of parameters in the report definition
            num_reports = get_pus_policy().housekeeping.count_type()
            num_reports.value = num_reports.from_bytes(app_data)
            offset = num_reports.size

            # parse report IDs
            report_id_dummy = get_pus_policy().housekeeping.structure_id_type()
            fmt = ">" + f"{num_reports.value}{report_id_dummy.format}".replace('>', '')
            report_ids = struct.unpack(fmt, app_data[offset:])

            for report_id in report_ids:
                if report_id in reports:
                    operation(report_id, reports, *argv)

        except struct.error:
            return CommonErrorCode.INCOMPLETE
        return True

    def _delete_reports(self, app_data, diagnostic=False):
        def operation(report_id, reports):
            if not reports[report_id].enabled:
                del reports[report_id]

        return self._for_each_report_id(app_data, diagnostic, operation)

    def _toggle_reports(self, app_data, diagnostic=False, enable=True):
        def operation(report_id, reports, enable):
            report = reports[report_id]
            if enable:
                report.enable()
            else:
                report.disable()

        return self._for_each_report_id(app_data, diagnostic, operation, enable)

    def _request_report_structures(self, app_data, diagnostic=False):
        raise NotImplementedError

    def _request_reports(self, app_data, diagnostic=False):
        raise NotImplementedError

    def _append_report(self, app_data, diagnostic=False):
        raise NotImplementedError

    def _modify_report_intervals(self, app_data, diagnostic=False):
        raise NotImplementedError

    def _request_interval_properties(self, app_data, diagnostic=False):
        raise NotImplementedError
