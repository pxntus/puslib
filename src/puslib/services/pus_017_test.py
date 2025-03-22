from typing import SupportsBytes

from puslib import get_policy
from puslib.ident import PusIdent
from puslib.streams.stream import OutputStream
from puslib.services import RequestVerification
from puslib.services.service import PusService, PusServiceType


class Test(PusService):
    """PUS service 17: Test service."""

    def __init__(self, ident: PusIdent, pus_service_1: RequestVerification, tm_output_stream: OutputStream):
        """Create a PUS service instance.

        Arguments:
            ident -- PUS identifier
            pus_service_1 -- PUS service 1 instance
            tm_output_stream -- output stream
        """
        super().__init__(PusServiceType.TEST, ident, pus_service_1, tm_output_stream)
        super()._register_sub_service(1, self.connection_test)

    def connection_test(self, app_data: SupportsBytes):  # pylint: disable=unused-argument
        """Response to a connection test request.

        Arguments:
            app_data -- application data

        Returns:
            subservice status
        """
        time = get_policy().CucTime()
        report = get_policy().PusTmPacket(
            apid=self._ident.apid,
            seq_count=self._ident.seq_count(),
            service_type=self._service_type.value,
            service_subtype=2,
            time=time
        )
        self._tm_output_stream.write(report)
        return True
