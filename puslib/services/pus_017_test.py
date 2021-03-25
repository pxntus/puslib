from datetime import datetime

from .service import PusService


class Test(PusService):
    def __init__(self, ident, pus_service_1, tm_distributor):
        super().__init__(self, 17)
        super()._register_sub_service(1, self.connection_test)

    def connection_test(self, packet):
        report = Test.pus_policy.create_tm_packet(
            apid=self._ident.apid,
            seq_count=self._ident.next_seq_count(),
            service_type=self._service_type.value,
            service_subtype=2,
            time=Test.pus_policy.time().from_datetime(datetime.utcnow())
        )
        return True, report
