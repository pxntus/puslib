import struct
from functools import partial

import pytest

from puslib import get_policy
from puslib.ident import PusIdent
from puslib.packet import PusTcPacket, AckFlag
from puslib.services import RequestVerification
from puslib.services.error_codes import CommonErrorCode
from puslib.streams.buffer import QueuedOutput


def unpack_payload(data):
    request_id = struct.Struct('>HH')
    failure_notice = struct.Struct(get_policy().request_verification.failure_code_type().format)
    if len(data) < request_id.size:
        assert False, "Invalid payload length"

    packet_id, packet_seq_ctrl = request_id.unpack(data[0:4])
    apid = packet_id & 0x07ff
    name = packet_seq_ctrl & 0x3ff
    if len(data) > request_id.size:
        code = failure_notice.unpack_from(data, request_id.size)[0]
        if len(data) > request_id.size + failure_notice.size:
            extra_data = data[request_id.size + failure_notice.size:]
    else:
        code = None
        extra_data = None
    return apid, name, code, extra_data


@pytest.fixture(name="service_1_setup")
def fixture_service_1_setup():
    ident = PusIdent(apid=10)
    tm_stream = QueuedOutput()
    pus_service_1 = RequestVerification(ident, tm_stream)
    TcPacket = partial(PusTcPacket.create, apid=ident.apid, name=0, ack_flags=AckFlag.NONE, service_type=8, service_subtype=1, data=bytes.fromhex("0000"))
    return pus_service_1, tm_stream, TcPacket


def test_no_ackflags(service_1_setup):
    pus_service_1, tm_stream, TcPacket = service_1_setup

    packet = TcPacket()
    pus_service_1.accept(packet)
    pus_service_1.start(packet)
    pus_service_1.progress(packet)
    pus_service_1.complete(packet)
    assert tm_stream.size == 0


def test_multiple_ackflags(service_1_setup):
    pus_service_1, tm_stream, TcPacket = service_1_setup

    packet = TcPacket(ack_flags=AckFlag.ACCEPTANCE | AckFlag.START_OF_EXECUTION | AckFlag.PROGRESS | AckFlag.COMPLETION)
    pus_service_1.accept(packet)
    pus_service_1.start(packet)
    pus_service_1.progress(packet)
    pus_service_1.complete(packet)
    assert tm_stream.size == 4


@pytest.mark.parametrize("service_1_setup, ack_flag, sub_service_success, sub_service_failure",
    [
        ("service_1_setup", AckFlag.ACCEPTANCE, 1, 2),
        ("service_1_setup", AckFlag.START_OF_EXECUTION, 3, 4),
        ("service_1_setup", AckFlag.PROGRESS, 5, 6),
        ("service_1_setup", AckFlag.COMPLETION, 7, 8),
    ],
    indirect=["service_1_setup"],
)
def test_accept(service_1_setup, ack_flag, sub_service_success, sub_service_failure):
    pus_service_1, tm_stream, TcPacket = service_1_setup

    if ack_flag == AckFlag.ACCEPTANCE:
        pus1_func = partial(pus_service_1.accept)
    elif ack_flag == AckFlag.START_OF_EXECUTION:
        pus1_func = partial(pus_service_1.start)
    elif ack_flag == AckFlag.PROGRESS:
        pus1_func = partial(pus_service_1.progress)
    elif ack_flag == AckFlag.COMPLETION:
        pus1_func = partial(pus_service_1.complete)

    packet = TcPacket(ack_flags=ack_flag)
    pus1_func(packet)
    assert tm_stream.size == 1
    report = tm_stream.get()
    assert report.service == 1
    assert report.subservice == sub_service_success

    apid, name, code, extra_data = unpack_payload(report.source_data)
    assert report.apid == apid
    assert packet.name == name
    assert code is None
    assert extra_data is None

    failure_code = CommonErrorCode.ILLEGAL_APP_DATA
    failure_extra_data = bytes.fromhex("abcd")
    pus1_func(packet, success=False, failure_code=failure_code, failure_data=failure_extra_data)
    assert tm_stream.size == 1
    report = tm_stream.get()
    assert report.service == 1
    assert report.subservice == sub_service_failure

    apid, name, code, extra_data = unpack_payload(report.source_data)
    assert report.apid == apid
    assert packet.name == name
    assert code == CommonErrorCode.ILLEGAL_APP_DATA.value
    assert extra_data == failure_extra_data
