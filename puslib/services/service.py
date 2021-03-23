import queue

from puslib.packet import AckFlag
from puslib.policy import PusPolicy
from .error_codes import CommonErrorCode


class PusService:
    pus_policy = PusPolicy

    def __init__(self, service_type, ident=None, pus_service_1=None, tm_distributor=None):
        self._service_type = service_type
        self._subservices = dict()
        self._ident = ident
        self._incoming_tc_queue = queue.SimpleQueue()
        self._tm_distributor = tm_distributor
        self._pus_service_1 = pus_service_1

    @property
    def service(self):
        return self._service_type.value

    @property
    def name(self):
        return self._service_type.name

    def enqueue(self, tc_packet):
        if tc_packet.apid == self._ident.apid and tc_packet.service == self.service and tc_packet.subservice in self._subservices:
            self._incoming_tc_queue.put(tc_packet)

    def process(self):
        while not self._incoming_tc_queue.empty():
            tc_packet = self._incoming_tc_queue.get()
            subservice_handler = self._subservices[tc_packet.subservice]
            success, pus_error_code = subservice_handler(tc_packet.app_data)
            if not success and not pus_error_code:
                pus_error_code = CommonErrorCode.ILLEGAL_APP_DATA.value

            if tc_packet.ack(AckFlag.ACCEPTANCE):
                self._pus_service_1.accept(tc_packet, code=pus_error_code, success=success)
            if tc_packet.ack(AckFlag.COMPLETION):
                self._pus_service_1.complete(tc_packet, code=pus_error_code, success=success)

    def _register_sub_service(self, number, callback):
        self._subservices[number] = callback
