from puslib.ident import PusIdent
from puslib.packet import PusTcPacket, AckFlag
from puslib.services import RequestVerification, PusService17
from puslib.streams.buffer import QueuedOutput


def test_are_you_alive_connection_test():
    ident = PusIdent(apid=10)
    tm_stream = QueuedOutput()
    pus_service_1 = RequestVerification(ident, tm_stream)
    test = PusService17(ident, pus_service_1, tm_stream)
    packet = PusTcPacket.create(apid=ident.apid, name=0, ack_flags=AckFlag.NONE, service_type=17, service_subtype=1)
    test.enqueue(packet)
    test.process()

    assert tm_stream.size == 1
    report = tm_stream.get()
    assert report.service == 17
    assert report.subservice == 2
    assert report.source_data is None
