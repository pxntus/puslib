import struct

import pytest

from puslib import get_pus_policy
from puslib.ident import PusIdent
from puslib.packet import PusTcPacket, AckFlag
from puslib.parameter import UInt32Parameter, Int16Parameter, Real64Parameter
from puslib.services import RequestVerification, PusService20
from puslib.streams.buffer import QueuedOutput


@pytest.fixture(name="service_20_setup")
def fixture_service_20_setup():
    ident = PusIdent(apid=10)
    tm_stream = QueuedOutput()
    pus_service_1 = RequestVerification(ident, tm_stream)

    params = {
        0: UInt32Parameter(1),
        3: Int16Parameter(-2),
        5: Real64Parameter(3.0)
    }

    pus_service_20 = PusService20(ident, pus_service_1, tm_stream, params)
    return pus_service_20, ident, tm_stream, params


def test_report_parameter_values(service_20_setup):
    pus_service_20, ident, tm_stream, _ = service_20_setup

    app_data = get_pus_policy().function_management.count_type(1).to_bytes() + get_pus_policy().common.param_id_type(0).to_bytes()
    packet = PusTcPacket.create(apid=ident.apid, name=0, ack_flags=AckFlag.NONE, service_type=20, service_subtype=1, data=app_data)
    pus_service_20.enqueue(packet)
    pus_service_20.process()
    assert tm_stream.size == 1
    report = tm_stream.get()
    assert report.service == 20
    assert report.subservice == 2
    assert report.source_data is not None
    fmt = '>' + (get_pus_policy().function_management.count_type().format + get_pus_policy().common.param_id_type().format + UInt32Parameter().format).replace('>', '')
    num_values, param_id, param_value = struct.unpack(fmt, report.source_data)
    assert num_values == 1
    assert param_id == 0
    assert param_value == 1

    app_data = get_pus_policy().function_management.count_type(2).to_bytes() + get_pus_policy().common.param_id_type(0).to_bytes() + get_pus_policy().common.param_id_type(3).to_bytes()
    packet = PusTcPacket.create(apid=ident.apid, name=0, ack_flags=AckFlag.NONE, service_type=20, service_subtype=1, data=app_data)
    pus_service_20.enqueue(packet)
    pus_service_20.process()
    assert tm_stream.size == 1
    report = tm_stream.get()
    assert report.service == 20
    assert report.subservice == 2
    assert report.source_data is not None
    fmt = '>' + (get_pus_policy().function_management.count_type().format + get_pus_policy().common.param_id_type().format + UInt32Parameter().format + get_pus_policy().common.param_id_type().format + Int16Parameter().format).replace('>', '')
    num_values, param1_id, param1_value, param2_id, param2_value = struct.unpack(fmt, report.source_data)
    assert num_values == 2
    assert param1_id == 0
    assert param1_value == 1
    assert param2_id == 3
    assert param2_value == -2

    app_data = get_pus_policy().function_management.count_type(1).to_bytes() + get_pus_policy().common.param_id_type(1).to_bytes()  # non-existant parameter ID
    packet = PusTcPacket.create(apid=ident.apid, name=0, ack_flags=AckFlag.ACCEPTANCE, service_type=20, service_subtype=1, data=app_data)
    pus_service_20.enqueue(packet)
    pus_service_20.process()
    assert tm_stream.size == 1
    report = tm_stream.get()
    assert report.service == 1
    assert report.subservice == 2

    app_data = get_pus_policy().function_management.count_type(2).to_bytes() + get_pus_policy().common.param_id_type(0).to_bytes() + get_pus_policy().common.param_id_type(1).to_bytes()  # non-existant parameter ID
    packet = PusTcPacket.create(apid=ident.apid, name=0, ack_flags=AckFlag.ACCEPTANCE, service_type=20, service_subtype=1, data=app_data)
    pus_service_20.enqueue(packet)
    pus_service_20.process()
    assert tm_stream.size == 1
    report = tm_stream.get()
    assert report.service == 1
    assert report.subservice == 2

    app_data = get_pus_policy().function_management.count_type(3).to_bytes() + get_pus_policy().common.param_id_type(0).to_bytes() + get_pus_policy().common.param_id_type(1).to_bytes()  # mismatch between N and number of parameter IDs
    packet = PusTcPacket.create(apid=ident.apid, name=0, ack_flags=AckFlag.ACCEPTANCE, service_type=20, service_subtype=1, data=app_data)
    pus_service_20.enqueue(packet)
    pus_service_20.process()
    assert tm_stream.size == 1
    report = tm_stream.get()
    assert report.service == 1
    assert report.subservice == 2


def test_set_parameter_values(service_20_setup):
    pus_service_20, ident, tm_stream, params = service_20_setup

    app_data = get_pus_policy().function_management.count_type(1).to_bytes() + get_pus_policy().common.param_id_type(0).to_bytes() + UInt32Parameter(11).to_bytes()
    packet = PusTcPacket.create(apid=ident.apid, name=0, ack_flags=AckFlag.NONE, service_type=20, service_subtype=3, data=app_data)
    pus_service_20.enqueue(packet)
    pus_service_20.process()
    assert tm_stream.size == 0
    assert params[0].value == 11
    assert params[3].value == -2
    assert params[5].value == 3.0

    app_data = get_pus_policy().function_management.count_type(2).to_bytes() + get_pus_policy().common.param_id_type(3).to_bytes() + Int16Parameter(-12).to_bytes() + get_pus_policy().common.param_id_type(5).to_bytes() + Real64Parameter(13.0).to_bytes()
    packet = PusTcPacket.create(apid=ident.apid, name=0, ack_flags=AckFlag.NONE, service_type=20, service_subtype=3, data=app_data)
    pus_service_20.enqueue(packet)
    pus_service_20.process()
    assert tm_stream.size == 0
    assert params[0].value == 11
    assert params[3].value == -12
    assert params[5].value == 13.0

    app_data = get_pus_policy().function_management.count_type(1).to_bytes() + get_pus_policy().common.param_id_type(1).to_bytes() + UInt32Parameter(11).to_bytes()  # non-existant parameter ID
    packet = PusTcPacket.create(apid=ident.apid, name=0, ack_flags=AckFlag.ACCEPTANCE, service_type=20, service_subtype=3, data=app_data)
    pus_service_20.enqueue(packet)
    pus_service_20.process()
    assert tm_stream.size == 1
    report = tm_stream.get()
    assert report.service == 1
    assert report.subservice == 2
    assert params[0].value == 11
    assert params[3].value == -12
    assert params[5].value == 13.0

    app_data = get_pus_policy().function_management.count_type(1).to_bytes() + get_pus_policy().common.param_id_type(1).to_bytes() + UInt32Parameter(1).to_bytes() + get_pus_policy().common.param_id_type(2).to_bytes() + UInt32Parameter(666).to_bytes()  # non-existant parameter ID
    packet = PusTcPacket.create(apid=ident.apid, name=0, ack_flags=AckFlag.ACCEPTANCE, service_type=20, service_subtype=3, data=app_data)
    pus_service_20.enqueue(packet)
    pus_service_20.process()
    assert tm_stream.size == 1
    report = tm_stream.get()
    assert report.service == 1
    assert report.subservice == 2
    assert params[0].value == 11
    assert params[3].value == -12
    assert params[5].value == 13.0
