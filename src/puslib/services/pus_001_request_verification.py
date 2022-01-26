from enum import IntEnum

from .. import get_pus_policy
from ..packet import AckFlag
from .service import PusService, PusServiceType
from .error_codes import CommonErrorCode


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
    def __init__(self, ident, tm_output_stream):
        super().__init__(PusServiceType.REQUEST_VERIFICATION, ident=ident, tm_output_stream=tm_output_stream)

    def enqueue(self, tc_packet):
        raise RuntimeError("Request verification service (PUS 1) doesn't have a TC queue")

    def process(self):
        raise RuntimeError("Request verification service (PUS 1) doesn't have a TC queue")

    def accept(self, packet, success=True, failure_code=None, failure_data=None):
        if not packet.ack(AckFlag.ACCEPTANCE):
            return
        self._generate_report(
            packet,
            _SubService.SUCCESSFUL_ACCEPTANCE_VERIFICATION if success else _SubService.FAILED_ACCEPTANCE_VERIFICATION,
            success,
            failure_code,
            failure_data)

    def start(self, packet, success=True, failure_code=None, failure_data=None):
        if not packet.ack(AckFlag.START_OF_EXECUTION):
            return
        self._generate_report(
            packet,
            _SubService.SUCCESSFUL_START_OF_EXECUTION_VERIFICATION if success else _SubService.FAILED_START_OF_EXECUTION_VERIFICATION,
            success,
            failure_code,
            failure_data)

    def progress(self, packet, success=True, failure_code=None, failure_data=None):
        if not packet.ack(AckFlag.PROGRESS):
            return
        self._generate_report(
            packet,
            _SubService.SUCCESSFUL_PROGRESS_OF_EXECUTION_VERIFICATION if success else _SubService.FAILED_PROGRESS_OF_EXECUTION_VERIFICATION,
            success,
            failure_code,
            failure_data)

    def complete(self, packet, success=True, failure_code=None, failure_data=None):
        if not packet.ack(AckFlag.COMPLETION):
            return
        self._generate_report(
            packet,
            _SubService.SUCCESSFUL_COMPLETION_OF_EXECUTION_VERIFICATION if success else _SubService.FAILED_COMPLETION_OF_EXECUTION_VERIFICATION,
            success,
            failure_code,
            failure_data)

    def _generate_report(self, packet, subservice, success, failure_code, failure_data):
        payload = packet.request_id()
        if not success:
            if not failure_code:
                failure_code = CommonErrorCode.ILLEGAL_APP_DATA
            payload += failure_code.value.to_bytes(get_pus_policy().request_verification.failure_code_type().size, byteorder='big') + (failure_data if failure_data else b'')
        time = get_pus_policy().CucTime()
        report = get_pus_policy().PusTmPacket(
            apid=self._ident.apid,
            seq_count=self._ident.seq_count(),
            service_type=self._service_type.value,
            service_subtype=subservice,
            time=time,
            data=payload
        )
        self._tm_output_stream.write(report)
