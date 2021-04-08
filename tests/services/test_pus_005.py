import struct

import pytest

from puslib import get_pus_policy
from puslib.ident import PusIdent
from puslib.packet import PusTcPacket, AckFlag
from puslib.parameter import UInt16Parameter, UInt32Parameter, UInt64Parameter
from puslib.services import RequestVerification, PusService5, Severity
from puslib.streams.buffer import QueuedOutput


@pytest.fixture
def service_5_setup():
    ident = PusIdent(apid=10)
    tm_stream = QueuedOutput()
    pus_service_1 = RequestVerification(ident, tm_stream)
    pus_service_5 = PusService5(ident, pus_service_1, tm_stream)
    return pus_service_5, tm_stream, ident


def test_manual_event(service_5_setup):
    pus_service_5, tm_stream, _ = service_5_setup

    ev = pus_service_5.add(0, Severity.INFO)
    assert tm_stream.empty()
    assert ev.id == 0
    assert ev.severity == Severity.INFO
    assert ev.enabled

    with pytest.raises(RuntimeError):
        pus_service_5.add(0, Severity.INFO)

    pus_service_5.dispatch(0)
    assert tm_stream.size == 1
    report = tm_stream.get()
    assert report.service == 5
    assert report.subservice == Severity.INFO
    assert len(report.source_data) == get_pus_policy().IdType().size
    id_param = get_pus_policy().IdType.from_bytes(report.source_data)
    assert id_param.value == 0

    pus_service_5.dispatch(ev)
    assert tm_stream.size == 1
    report = tm_stream.get()
    assert report.service == 5
    assert report.subservice == Severity.INFO

    ev.disable()
    pus_service_5.dispatch(ev)
    assert tm_stream.empty()

    with pytest.raises(RuntimeError):
        pus_service_5.dispatch(10)


def test_event_with_data(service_5_setup):
    pus_service_5, tm_stream, _ = service_5_setup

    param1 = UInt32Parameter(4)
    param2 = UInt16Parameter(5)
    param3 = UInt64Parameter(6)
    ev = pus_service_5.add(3, Severity.INFO, params_in_report=[param1, param2, param3])

    pus_service_5.dispatch(ev)
    assert tm_stream.size == 1
    report = tm_stream.get()
    id_param = get_pus_policy().IdType()
    assert len(report.source_data) == (id_param.size + param1.size + param2.size + param3.size)
    fmt = '>' + (id_param.format + param1.format + param2.format + param3.format).replace('>', '')
    id_param.value, param1.value, param2.value, param3.value = struct.unpack(fmt, report.source_data)
    assert id_param.value == 3
    assert param1.value == 4
    assert param2.value == 5
    assert param3.value == 6


def test_trigger_events(service_5_setup):
    pus_service_5, tm_stream, _ = service_5_setup

    param1 = UInt32Parameter(0)
    ev = pus_service_5.add(3, Severity.INFO, None, enabled=True, trig_param=param1)
    assert tm_stream.size == 0
    param1.value += 1
    assert tm_stream.size == 1
    report = tm_stream.get()
    assert report.service == 5
    assert report.subservice == Severity.INFO
    id_param = get_pus_policy().IdType.from_bytes(report.source_data)
    assert id_param.value == 3
    ev.disable()
    param1.value += 1
    assert tm_stream.size == 0

    param2 = UInt32Parameter(0)
    pus_service_5.add(5, Severity.LOW, None, enabled=True, trig_param=param2, to_value=2)
    param2.value += 1
    assert tm_stream.size == 0
    param2.value += 1
    assert tm_stream.size == 1
    report = tm_stream.get()
    assert report.service == 5
    assert report.subservice == Severity.LOW
    id_param = get_pus_policy().IdType.from_bytes(report.source_data)
    assert id_param.value == 5

    param3 = UInt32Parameter(0)
    pus_service_5.add(7, Severity.MEDIUM, None, enabled=True, trig_param=param3, to_value=1, from_value=2)
    param3.value += 1
    assert tm_stream.size == 0
    param3.value += 1
    assert tm_stream.size == 0
    param3.value -= 1
    assert tm_stream.size == 1
    report = tm_stream.get()
    assert report.service == 5
    assert report.subservice == Severity.MEDIUM
    id_param = get_pus_policy().IdType.from_bytes(report.source_data)
    assert id_param.value == 7


def test_toggle_event(service_5_setup):
    pus_service_5, tm_stream, _ = service_5_setup

    ev1 = pus_service_5.add(0, Severity.INFO)
    ev2 = pus_service_5.add(1, Severity.LOW, params_in_report=None, enabled=False)
    ev3 = pus_service_5.add(2, Severity.MEDIUM)
    ev4 = pus_service_5.add(3, Severity.HIGH)

    assert ev1.enabled
    assert not ev2.enabled
    assert ev3.enabled
    assert ev4.enabled

    ev1.disable()
    ev2.enable()
    ev3.disable()

    assert not ev1.enabled
    assert ev2.enabled
    assert not ev3.enabled
    assert ev4.enabled


def test_disabled_event_report(service_5_setup):
    pus_service_5, tm_stream, ident = service_5_setup

    packet = PusTcPacket.create(apid=ident.apid, name=0, ack_flags=AckFlag.NONE, service_type=5, service_subtype=7)
    pus_service_5.enqueue(packet)
    pus_service_5.process()
    assert tm_stream.size == 1
    report = tm_stream.get()
    assert report.service == 5
    assert report.subservice == 8
    assert len(report.source_data) == get_pus_policy().NType().size
    num_events_param = get_pus_policy().NType.from_bytes(report.source_data)
    assert num_events_param.value == 0

    ev1 = pus_service_5.add(1, Severity.INFO)
    ev2 = pus_service_5.add(2, Severity.LOW)
    ev3 = pus_service_5.add(3, Severity.MEDIUM)
    ev4 = pus_service_5.add(4, Severity.HIGH)

    pus_service_5.enqueue(packet)
    pus_service_5.process()
    assert tm_stream.size == 1
    report = tm_stream.get()
    assert report.service == 5
    assert report.subservice == 8
    assert len(report.source_data) == get_pus_policy().NType().size

    ev2.disable()
    ev4.disable()

    pus_service_5.enqueue(packet)
    pus_service_5.process()
    assert tm_stream.size == 1
    report = tm_stream.get()
    assert report.service == 5
    assert report.subservice == 8
    assert len(report.source_data) == get_pus_policy().NType().size + get_pus_policy().IdType().size * 2
    fmt = '>' + f"{get_pus_policy().NType().format}2{get_pus_policy().IdType().format}".replace('>', '')
    num_events, id1, id2 = struct.unpack(fmt, report.source_data)
    assert num_events == 2
    assert id1 == 2
    assert id2 == 4

    ev1.disable()
    ev3.disable()

    pus_service_5.enqueue(packet)
    pus_service_5.process()
    assert tm_stream.size == 1
    report = tm_stream.get()
    assert report.service == 5
    assert report.subservice == 8
    assert len(report.source_data) == get_pus_policy().NType().size + get_pus_policy().IdType().size * 4
    fmt = '>' + f"{get_pus_policy().NType().format}4{get_pus_policy().IdType().format}".replace('>', '')
    num_events, id1, id2, id3, id4 = struct.unpack(fmt, report.source_data)
    assert num_events == 4
    assert id1 == 1
    assert id2 == 2
    assert id3 == 3
    assert id4 == 4
