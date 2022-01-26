import struct
from functools import partial
from collections import OrderedDict

from .service import PusService, PusServiceType
from .param_report import ParamReport
from .error_codes import CommonErrorCode
from .. import get_pus_policy


class Report(ParamReport):
    def __init__(self, sid, collection_interval, enabled=True, params_in_report=None):
        super().__init__(sid, enabled, params_in_report)
        self._collection_interval = collection_interval

    @property
    def collection_interval(self):
        return self._collection_interval

    @collection_interval.setter
    def collection_interval(self, new_value):
        self._collection_interval = new_value


class Housekeeping(PusService):
    def __init__(self, ident, pus_service_1, tm_output_stream, params):
        super().__init__(PusServiceType.HOUSEKEEPING, ident, pus_service_1, tm_output_stream)
        self._params = params
        self._housekeeping_reports = {}
        self._diagnostic_reports = {}
        self._register_sub_service(1, partial(self._create_or_append_report, append=False, diagnostic=False))
        self._register_sub_service(2, partial(self._create_or_append_report, append=False, diagnostic=True))
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
        self._register_sub_service(29, partial(self._create_or_append_report, append=True, diagnostic=False))
        self._register_sub_service(30, partial(self._create_or_append_report, append=True, diagnostic=True))
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

    @staticmethod
    def create_parameter_report(apid, seq_count, report, diagnostic=False):
        app_data = report.to_bytes()
        packet = get_pus_policy().PusTmPacket(
            apid=apid,
            seq_count=seq_count,
            service_type=PusServiceType.HOUSEKEEPING.value,
            service_subtype=26 if diagnostic else 25,
            time=get_pus_policy().CucTime(),
            data=app_data
        )
        return packet

    @staticmethod
    def create_structure_report(apid, seq_count, report, diagnostic=False):
        app_data = get_pus_policy().housekeeping.structure_id_type(report.id).to_bytes() + \
            get_pus_policy().housekeeping.collection_interval_type(report.collection_interval).to_bytes() + \
            get_pus_policy().housekeeping.count_type(len(report)).to_bytes()
        for pid, _ in report:
            app_data += get_pus_policy().common.param_id_type(pid).to_bytes()
        app_data += get_pus_policy().housekeeping.count_type(0).to_bytes()
        packet = get_pus_policy().PusTmPacket(
            apid=apid,
            seq_count=seq_count,
            service_type=PusServiceType.HOUSEKEEPING.value,
            service_subtype=12 if diagnostic else 10,
            time=get_pus_policy().CucTime(),
            data=app_data
        )
        return packet

    @staticmethod
    def create_periodic_generation_properties_report(apid, seq_count, reports_to_report, diagnostic=False):
        app_data = get_pus_policy().housekeeping.count_type(len(reports_to_report)).to_bytes()
        for report in reports_to_report:
            app_data += get_pus_policy().housekeeping.structure_id_type(report.id).to_bytes() + \
                get_pus_policy().housekeeping.periodic_generation_action_status_type(1 if report.enabled else 0).to_bytes() + \
                get_pus_policy().housekeeping.collection_interval_type(report.collection_interval).to_bytes()
        packet = get_pus_policy().PusTmPacket(
            apid=apid,
            seq_count=seq_count,
            service_type=PusServiceType.HOUSEKEEPING.value,
            service_subtype=36 if diagnostic else 35,
            time=get_pus_policy().CucTime(),
            data=app_data
        )
        return packet

    def _create_or_append_report(self, app_data, append=False, diagnostic=False):
        reports = self._diagnostic_reports if diagnostic else self._housekeeping_reports

        try:
            sid = get_pus_policy().housekeeping.structure_id_type()
            sid.value = sid.from_bytes(app_data)
            if append:
                if sid.value not in reports:
                    return CommonErrorCode.PUS3_SID_NOT_PRESENT
                if reports[sid.value].enabled:
                    return CommonErrorCode.PUS3_CANNOT_MODIFY_ENABLED_REPORT
            else:
                if sid.value in reports:
                    return CommonErrorCode.PUS3_SID_ALREADY_PRESENT
            offset = sid.size

            if not append:
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
            param_ids = struct.unpack(fmt, app_data[offset:offset + struct.calcsize(fmt)])
            if len(param_ids) != len(set(param_ids)):
                return CommonErrorCode.PUS3_PARAM_DUPLICATION
            param_ids = [param_id for param_id in param_ids if param_id in self._params]
            offset += struct.calcsize(fmt)

            # parse number of fixed-length arrays
            nfa = get_pus_policy().housekeeping.count_type()
            nfa.value = nfa.from_bytes(app_data[offset:])
            if nfa.value != 0:
                raise NotImplementedError  # super commutated parameters is not supported

            params = OrderedDict([(param_id, self._params[param_id]) for param_id in param_ids])
            if append:
                reports[sid.value].append(params)
            else:
                reports[sid.value] = Report(sid=sid.value, collection_interval=collection_interval.value, enabled=False, params_in_report=params)
            return True

        except struct.error:
            return CommonErrorCode.INCOMPLETE

    def _for_each_report_id(self, app_data, diagnostic, operation, *argv):
        """Help function to simplify handling of requests with N report IDs.

        The request, or command, should have the following structure:

            +-------+---------------+-----------------+---------+---------------+
            |   N   | Report ID [N] | Report ID [N-1] |   ...   | Report ID [1] |
            +-------+---------------+-----------------+---------+---------------+

        where N is the number of report IDs in the request.
        """
        try:
            # parse number of parameters in the report definition
            num_reports = get_pus_policy().housekeeping.count_type()
            num_reports.value = num_reports.from_bytes(app_data)
            offset = num_reports.size

            # parse report IDs
            report_id_dummy = get_pus_policy().housekeeping.structure_id_type()
            fmt = ">" + f"{num_reports.value}{report_id_dummy.format}".replace('>', '')
            report_ids = struct.unpack(fmt, app_data[offset:])

            reports = self._diagnostic_reports if diagnostic else self._housekeeping_reports
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
        def operation(report_id, reports):
            report = reports[report_id]
            packet = Housekeeping.create_structure_report(self._ident.apid, self._ident.seq_count(), report, diagnostic)
            self._tm_output_stream.write(packet)

        return self._for_each_report_id(app_data, diagnostic, operation)

    def _request_reports(self, app_data, diagnostic=False):
        def operation(report_id, reports):
            report = reports[report_id]
            packet = Housekeeping.create_parameter_report(self._ident.apid, self._ident.seq_count(), report, diagnostic)
            self._tm_output_stream.write(packet)

        return self._for_each_report_id(app_data, diagnostic, operation)

    def _modify_report_intervals(self, app_data, diagnostic=False):
        reports = self._diagnostic_reports if diagnostic else self._housekeeping_reports
        try:
            n = get_pus_policy().housekeeping.count_type()
            n.value = n.from_bytes(app_data)
            offset = n.size
            for _ in range(n.value):
                sid = get_pus_policy().housekeeping.structure_id_type()
                sid.value = sid.from_bytes(app_data[offset:])
                offset += sid.size
                collection_interval = get_pus_policy().housekeeping.collection_interval_type()
                collection_interval.value = collection_interval.from_bytes(app_data[offset:])

                if sid in reports:
                    reports[sid].collection_interval = collection_interval.value

            return True

        except struct.error:
            return CommonErrorCode.INCOMPLETE

    def _request_interval_properties(self, app_data, diagnostic=False):
        try:
            # parse number of parameters in the report definition
            num_reports = get_pus_policy().housekeeping.count_type()
            num_reports.value = num_reports.from_bytes(app_data)
            offset = num_reports.size

            # parse report IDs
            report_id_dummy = get_pus_policy().housekeeping.structure_id_type()
            fmt = ">" + f"{num_reports.value}{report_id_dummy.format}".replace('>', '')
            report_ids = struct.unpack(fmt, app_data[offset:])

            reports = self._diagnostic_reports if diagnostic else self._housekeeping_reports
            reports_to_report = [reports[sid] for sid in report_ids if sid in reports]
            packet = Housekeeping.create_periodic_generation_properties_report(self._ident.apid, self._ident.seq_count(), reports_to_report, diagnostic)
            self._tm_output_stream.write(packet)
            return True

        except struct.error:
            return CommonErrorCode.INCOMPLETE
