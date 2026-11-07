"""Example of a custom (mission-specific) PUS service.

Mission-specific services should use service types 128-255. Service types
below 128 are reserved for standard PUS services and trigger a warning.
"""
import sched

from puslib import get_policy
from puslib.ident import PusIdent
from puslib.process import Process
from puslib.services import RequestVerification
from puslib.services.service import PusService
from puslib.streams.console import ConsoleOutput
from puslib.streams.stream import OutputStream

MISSION_SERVICE = 130


class MissionService(PusService):
    """Mission-specific service with one request, TC(130,1), and one report, TM(130,2)."""

    def __init__(self, ident: PusIdent, pus_service_1: RequestVerification, tm_output_stream: OutputStream):
        super().__init__(MISSION_SERVICE, ident, pus_service_1, tm_output_stream,
                         name="Mission", description="Mission-specific service")
        self._tm_output_stream: OutputStream
        self._register_sub_service(1, self._echo)

    def _echo(self, app_data: bytes | bytearray) -> bool:
        """Echo the application data back in a report."""
        report = get_policy().PusTmPacket(
            apid=self._ident.apid,
            seq_count=self._ident.next_seq_count(),
            service_type=self.service,
            service_subtype=2,
            time=get_policy().CucTime(),
            data=bytes(app_data),
        )
        self._tm_output_stream.write(report)
        return True


tm_output_stream = ConsoleOutput()
scheduler = sched.scheduler()
process = Process(10, tm_output_stream, scheduler)
process.add_service(MissionService)  # class serves as factory

tc_packet = get_policy().PusTcPacket(
    apid=10,
    name=0,
    service_type=MISSION_SERVICE,
    service_subtype=1,
    data=b"hello",
)
process.forward(tc_packet)
