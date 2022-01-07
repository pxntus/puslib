import pytest

from puslib import get_pus_policy
from puslib.ident import PusIdent
from puslib.packet import PusTcPacket, AckFlag
from puslib.parameter import UInt16Parameter, UInt32Parameter, UInt64Parameter
from puslib.services import RequestVerification, Housekeeping
from puslib.streams.buffer import QueuedOutput


@pytest.fixture
def service_3_setup():
    ident = PusIdent(apid=10)
    tm_stream = QueuedOutput()
    pus_service_1 = RequestVerification(ident, tm_stream)
    params = {0: UInt32Parameter(4), 3: UInt16Parameter(5), 7: UInt64Parameter(6)}
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
    pus_service_3, tm_stream, ident, params = service_3_setup

    app_data = get_pus_policy().housekeeping.structure_id_type(1).to_bytes() + \
        get_pus_policy().housekeeping.collection_interval_type(500).to_bytes() + \
        get_pus_policy().housekeeping.count_type(3).to_bytes()
    for param_id, _ in params.items():
        app_data +=  get_pus_policy().common.param_id_type(param_id).to_bytes()
    app_data += get_pus_policy().housekeeping.count_type(0).to_bytes()
    packet = PusTcPacket.create(apid=ident.apid, name=0, ack_flags=AckFlag.NONE, service_type=3, service_subtype=2 if is_diagnostic_report else 1, data=app_data)

    pus_service_3.enqueue(packet)
    pus_service_3.process()

    reports = pus_service_3._diagnostic_reports if is_diagnostic_report else pus_service_3._housekeeping_reports
    assert reports is not None
    assert 1 in reports
    report = reports[1]
    assert report.id == 1
    assert report.collection_interval == 500
    assert len(report._params) == 3


@pytest.mark.parametrize("service_3_setup, is_diagnostic_report",
    [
        ("service_3_setup", True),
        ("service_3_setup", False),
    ],
    indirect=["service_3_setup"],
)
def test_delete_report(service_3_setup, is_diagnostic_report):
    pus_service_3, tm_stream, ident, params = service_3_setup
    report = pus_service_3.add(sid=1, collection_interval=1000, params_in_report=params.values(), enabled=True, diagnostic=is_diagnostic_report)
    reports = pus_service_3._diagnostic_reports if is_diagnostic_report else pus_service_3._housekeeping_reports
    assert len(reports) == 1

    # Delete non-existant report with SID = 0
    app_data = get_pus_policy().housekeeping.count_type(1).to_bytes() + \
        get_pus_policy().housekeeping.structure_id_type(0).to_bytes()
    packet = PusTcPacket.create(apid=ident.apid, name=0, ack_flags=AckFlag.NONE, service_type=3, service_subtype=4 if is_diagnostic_report else 3, data=app_data)
    pus_service_3.enqueue(packet)
    pus_service_3.process()
    assert len(reports) == 1

    # Delete report with SID = 1
    app_data = get_pus_policy().housekeeping.count_type(1).to_bytes() + \
        get_pus_policy().housekeeping.structure_id_type(1).to_bytes()
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
    pus_service_3, tm_stream, ident, params = service_3_setup
    report = pus_service_3.add(sid=1, collection_interval=1000, params_in_report=params.values(), enabled=False, diagnostic=is_diagnostic_report)
    assert not report.enabled

    # Enable report with SID = 1
    app_data = get_pus_policy().housekeeping.count_type(1).to_bytes() + \
        get_pus_policy().housekeeping.structure_id_type(1).to_bytes()
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
    pus_service_3, tm_stream, ident, params = service_3_setup
    report = pus_service_3.add(sid=1, collection_interval=1000, params_in_report=params.values(), enabled=True, diagnostic=is_diagnostic_report)
    assert report.enabled

    # Enable report with SID = 1
    app_data = get_pus_policy().housekeeping.count_type(1).to_bytes() + \
        get_pus_policy().housekeeping.structure_id_type(1).to_bytes()
    packet = PusTcPacket.create(apid=ident.apid, name=0, ack_flags=AckFlag.NONE, service_type=3, service_subtype=8 if is_diagnostic_report else 6, data=app_data)
    pus_service_3.enqueue(packet)
    pus_service_3.process()
    assert not report.enabled

    pus_service_3.enqueue(packet)
    pus_service_3.process()
    assert not report.enabled
