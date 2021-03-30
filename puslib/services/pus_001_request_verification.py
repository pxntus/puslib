from enum import IntEnum

from .service import PusService, PusServiceType


class _SubService(IntEnum):
    SUCCESSFUL_ACCEPTANCE_VERIFICATION = 1
    FAILED_ACCEPTANCE_VERIFICATION = 2
    SUCCESSFUL_START_OF_EXECUTION_VERIFICATION = 3
    FAILED_START_OF_EXECUTION_VERIFICATION = 4
    SUCCESSFUL_PROGRESS_OF_EXECUTION_VERIFICATION = 5
    FAILED_PROGRESS_OF_EXECUTION_VERIFICATION = 6
    SUCCESSFUL_COMPLETION_OF_EXECUTION_VERIFICATION = 7
    FAILED_COMPLETION_OF_EXECUTION_VERIFICATION = 8


class RequestVerification(PusService):
    def __init__(self, ident, tm_distributor):
        super().__init__(PusServiceType.REQUEST_VERIFICATION, ident=ident, tm_distributor=tm_distributor)

    def enqueue(self, tc_packet):
        raise RuntimeError("Request verification service (PUS 1) doesn't have a TC queue")

    def process(self):
        raise RuntimeError("Request verification service (PUS 1) doesn't have a TC queue")

    def accept(self, packet, code=None, success=True, failure_data=None):
        self._generate_report(
            packet,
            _SubService.SUCCESSFUL_ACCEPTANCE_VERIFICATION if success else _SubService.FAILED_ACCEPTANCE_VERIFICATION,
            code,
            success,
            failure_data)

    def start(self, packet, code=None, success=True, failure_data=None):
        self._generate_report(
            packet,
            _SubService.SUCCESSFUL_START_OF_EXECUTION_VERIFICATION if success else _SubService.FAILED_START_OF_EXECUTION_VERIFICATION,
            code,
            success,
            failure_data)

    def progress(self, packet, code=None, success=True, failure_data=None):
        self._generate_report(
            packet,
            _SubService.SUCCESSFUL_PROGRESS_OF_EXECUTION_VERIFICATION if success else _SubService.FAILED_PROGRESS_OF_EXECUTION_VERIFICATION,
            code,
            success,
            failure_data)

    def complete(self, packet, code=None, success=True, failure_data=None):
        self._generate_report(
            packet,
            _SubService.SUCCESSFUL_COMPLETION_OF_EXECUTION_VERIFICATION if success else _SubService.FAILED_COMPLETION_OF_EXECUTION_VERIFICATION,
            code,
            success,
            failure_data)

    def _generate_report(self, packet, subservice, code, success, failure_data):
        payload = packet.request_id()
        if not success:
            payload += code.to_bytes(1, byteorder='big') + (failure_data if failure_data else b'')
        time = PusService.pus_policy.time()
        report = PusService.pus_policy.create_tm_packet(
            apid=self._ident.apid,
            seq_count=self._ident.seq_count(),
            service_type=self._service_type.value,
            service_subtype=subservice,
            time=time,
            data=payload
        )
        self._tm_distributor.send(report)
