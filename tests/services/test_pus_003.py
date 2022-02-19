import struct
from collections import OrderedDict

import pytest

from puslib import get_policy
from puslib.ident import PusIdent
from puslib.packet import PusTcPacket, AckFlag
from puslib.parameter import UInt16Parameter, UInt32Parameter, UInt64Parameter
from puslib.services import RequestVerification, Housekeeping
from puslib.streams.buffer import QueuedOutput


@pytest.fixture(name="service_3_setup")
def fixture_service_3_setup():
    ident = PusIdent(apid=10)
    tm_stream = QueuedOutput()
    pus_service_1 = RequestVerification(ident, tm_stream)
    params = OrderedDict([(0, UInt32Parameter(4)), (4, UInt16Parameter(5)), (7, UInt64Parameter(6))])
    pus_service_3 = Housekeeping(ident, pus_service_1, tm_stream, params)
    return pus_service_3, tm_stream, ident, params


@pytest.mark.parametrize("service_3_setup, is_diagnostic_report",
    [
        ("service_3_setup", True),
        ("service_3_setup", False),
    ],
    indirect=["service_3_setup"],
)
def test_create_report(service_3_setup, is_diagnostic_report):
    pus_service_3, _, ident, params = service_3_setup

    app_data = get_policy().housekeeping.structure_id_type(1).to_bytes() + \
        get_policy().housekeeping.collection_interval_type(500).to_bytes() + \
        get_policy().housekeeping.count_type(3).to_bytes()
    for param_id, _ in params.items():
        app_data += get_policy().common.param_id_type(param_id).to_bytes()
    app_data += get_policy().housekeeping.count_type(0).to_bytes()
    packet = PusTcPacket.create(apid=ident.apid, name=0, ack_flags=AckFlag.NONE, service_type=3, service_subtype=2 if is_diagnostic_report else 1, data=app_data)

    pus_service_3.enqueue(packet)
    pus_service_3.process()

    reports = pus_service_3._diagnostic_reports if is_diagnostic_report else pus_service_3._housekeeping_reports  # pylint: disable=protected-access
    assert reports is not None
    assert 1 in reports
    report = reports[1]
    assert report.id == 1
    assert report.collection_interval == 500
    assert len(report._params) == 3  # pylint: disable=protected-access


@pytest.mark.parametrize("service_3_setup, is_diagnostic_report",
    [
        ("service_3_setup", True),
        ("service_3_setup", False),
    ],
    indirect=["service_3_setup"],
)
def test_delete_report(service_3_setup, is_diagnostic_report):
    pus_service_3, _, ident, params = service_3_setup
    report = pus_service_3.add(sid=1, collection_interval=1000, params_in_report=params, enabled=True, diagnostic=is_diagnostic_report)
    reports = pus_service_3._diagnostic_reports if is_diagnostic_report else pus_service_3._housekeeping_reports  # pylint: disable=protected-access
    assert len(reports) == 1

    # Delete non-existant report with SID = 0
    app_data = get_policy().housekeeping.count_type(1).to_bytes() + \
        get_policy().housekeeping.structure_id_type(0).to_bytes()
    packet = PusTcPacket.create(apid=ident.apid, name=0, ack_flags=AckFlag.NONE, service_type=3, service_subtype=4 if is_diagnostic_report else 3, data=app_data)
    pus_service_3.enqueue(packet)
    pus_service_3.process()
    assert len(reports) == 1

    # Delete report with SID = 1
    app_data = get_policy().housekeeping.count_type(1).to_bytes() + \
        get_policy().housekeeping.structure_id_type(1).to_bytes()
    packet = PusTcPacket.create(apid=ident.apid, name=0, ack_flags=AckFlag.NONE, service_type=3, service_subtype=4 if is_diagnostic_report else 3, data=app_data)
    pus_service_3.enqueue(packet)
    pus_service_3.process()
    assert len(reports) == 1  # fail since report is enabled
    report.disable()
    pus_service_3.enqueue(packet)
    pus_service_3.process()
    assert len(reports) == 0


@pytest.mark.parametrize("service_3_setup, is_diagnostic_report",
    [
        ("service_3_setup", True),
        ("service_3_setup", False),
    ],
    indirect=["service_3_setup"],
)
def test_enable_report(service_3_setup, is_diagnostic_report):
    pus_service_3, _, ident, params = service_3_setup
    report = pus_service_3.add(sid=1, collection_interval=1000, params_in_report=params, enabled=False, diagnostic=is_diagnostic_report)
    assert not report.enabled

    # Enable report with SID = 1
    app_data = get_policy().housekeeping.count_type(1).to_bytes() + \
        get_policy().housekeeping.structure_id_type(1).to_bytes()
    packet = PusTcPacket.create(apid=ident.apid, name=0, ack_flags=AckFlag.NONE, service_type=3, service_subtype=7 if is_diagnostic_report else 5, data=app_data)
    pus_service_3.enqueue(packet)
    pus_service_3.process()
    assert report.enabled

    pus_service_3.enqueue(packet)
    pus_service_3.process()
    assert report.enabled


@pytest.mark.parametrize("service_3_setup, is_diagnostic_report",
    [
        ("service_3_setup", True),
        ("service_3_setup", False),
    ],
    indirect=["service_3_setup"],
)
def test_disable_report(service_3_setup, is_diagnostic_report):
    pus_service_3, _, ident, params = service_3_setup
    report = pus_service_3.add(sid=1, collection_interval=1000, params_in_report=params, enabled=True, diagnostic=is_diagnostic_report)
    assert report.enabled

    # Disable report with SID = 1
    app_data = get_policy().housekeeping.count_type(1).to_bytes() + \
        get_policy().housekeeping.structure_id_type(1).to_bytes()
    packet = PusTcPacket.create(apid=ident.apid, name=0, ack_flags=AckFlag.NONE, service_type=3, service_subtype=8 if is_diagnostic_report else 6, data=app_data)
    pus_service_3.enqueue(packet)
    pus_service_3.process()
    assert not report.enabled

    pus_service_3.enqueue(packet)
    pus_service_3.process()
    assert not report.enabled


@pytest.mark.parametrize("service_3_setup, is_diagnostic_report",
    [
        ("service_3_setup", True),
        ("service_3_setup", False),
    ],
    indirect=["service_3_setup"],
)
def test_structure_report(service_3_setup, is_diagnostic_report):
    pus_service_3, tm_stream, ident, params = service_3_setup
    pus_service_3.add(sid=1, collection_interval=1000, params_in_report=params, enabled=True, diagnostic=is_diagnostic_report)

    # Request structure report
    app_data = get_policy().housekeeping.count_type(1).to_bytes() + \
        get_policy().housekeeping.structure_id_type(1).to_bytes()
    packet = PusTcPacket.create(apid=ident.apid, name=0, ack_flags=AckFlag.NONE, service_type=3, service_subtype=11 if is_diagnostic_report else 9, data=app_data)
    pus_service_3.enqueue(packet)
    pus_service_3.process()

    assert tm_stream.size == 1
    tm = tm_stream.get()
    assert tm.service == 3
    assert tm.subservice == 12 if is_diagnostic_report else 10
    fmt = '>' + f"{get_policy().housekeeping.structure_id_type().format}{get_policy().housekeeping.collection_interval_type().format}{get_policy().housekeeping.count_type().format}".replace('>', '')
    sid, collection_interval, num_params = struct.unpack(fmt, tm.source_data[:struct.calcsize(fmt)])
    assert sid == 1
    assert collection_interval == 1000
    assert num_params == 3
    fmt2 = '>' + f"{num_params}{get_policy().common.param_id_type().format}".replace('>', '')
    param_ids = struct.unpack(fmt2, tm.source_data[struct.calcsize(fmt):struct.calcsize(fmt) + struct.calcsize(fmt2)])
    for pid, ref_pid in zip(param_ids, params.keys()):
        assert pid == ref_pid


@pytest.mark.parametrize("service_3_setup, is_diagnostic_report",
    [
        ("service_3_setup", True),
        ("service_3_setup", False),
    ],
    indirect=["service_3_setup"],
)
def test_parameter_report(service_3_setup, is_diagnostic_report):
    pus_service_3, tm_stream, ident, params = service_3_setup
    pus_service_3.add(sid=1, collection_interval=1000, params_in_report=params, enabled=True, diagnostic=is_diagnostic_report)

    # Request parameter report
    app_data = get_policy().housekeeping.count_type(1).to_bytes() + \
        get_policy().housekeeping.structure_id_type(1).to_bytes()
    packet = PusTcPacket.create(apid=ident.apid, name=0, ack_flags=AckFlag.NONE, service_type=3, service_subtype=28 if is_diagnostic_report else 27, data=app_data)
    pus_service_3.enqueue(packet)
    pus_service_3.process()

    assert tm_stream.size == 1
    tm = tm_stream.get()
    assert tm.service == 3
    assert tm.subservice == 26 if is_diagnostic_report else 25
    fmt = f"{get_policy().housekeeping.structure_id_type().format}"
    for param in params.values():
        fmt += f"{param.format}"
    fmt = '>' + fmt.replace('>', '')
    sid, value1, value2, value3 = struct.unpack(fmt, tm.source_data[:struct.calcsize(fmt)])
    assert sid == 1
    assert value1 == 4
    assert value2 == 5
    assert value3 == 6
