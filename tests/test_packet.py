from collections import namedtuple

import pytest

from puslib.packet import CcsdsSpacePacket
from puslib.packet import PusTcPacket
from puslib.packet import PusTmPacket
from puslib.packet import PacketType
from puslib.packet import AckFlag
from puslib.time import CucTime

APID = 0x10
SEQ_COUNT_OR_NAME = 0x50
PUS_SERVICE = 8
PUS_SUBSERVICE = 1
TC_SOURCE = 0x2021
DATA = bytes.fromhex('DEADBEEF')

CcsdsPacketArgs = namedtuple('CcsdsPacketArgs', ['packet_version_number', 'packet_type', 'secondary_header_flag', 'apid', 'seq_flags', 'seq_count_or_name', 'data', 'has_pec'])


@pytest.mark.parametrize("args", [
    CcsdsPacketArgs(None, PacketType.TC, None, APID, None, SEQ_COUNT_OR_NAME, b'', True),
    CcsdsPacketArgs(None, PacketType.TC, None, APID, None, SEQ_COUNT_OR_NAME, b'', False),
    CcsdsPacketArgs(0, PacketType.TM, True, APID, 0b11, SEQ_COUNT_OR_NAME, DATA, True),
    CcsdsPacketArgs(0, PacketType.TM, False, APID, 0b11, SEQ_COUNT_OR_NAME, DATA, False),
])
def test_create_ccsds_packet(args):
    args_to_pass = {k: v for k, v in args._asdict().items() if v is not None}

    packet = CcsdsSpacePacket.create(**args_to_pass)
    assert packet.header.packet_version_number == args.packet_version_number if args.packet_version_number else 1
    assert packet.header.packet_type == args.packet_type
    assert packet.packet_type == args.packet_type
    assert packet.header.secondary_header_flag == args.secondary_header_flag if args.secondary_header_flag else True
    assert packet.header.apid == args.apid
    assert packet.apid == args.apid
    assert packet.header.seq_flags == args.seq_flags if args.seq_flags else 0b11
    assert packet.header.seq_count_or_name == args.seq_count_or_name
    assert packet.payload == args.data
    assert len(packet) == 6 + (len(args.data) if args.data else 0) + (2 if args.has_pec else 0)


TcPacketArgs = namedtuple('TcPacketArgs', ['apid', 'name', 'pus_version', 'ack_flags', 'service_type', 'service_subtype', 'source', 'data', 'has_pec'])


@pytest.mark.parametrize("args", [
    TcPacketArgs(APID, SEQ_COUNT_OR_NAME, 1, AckFlag.ACCEPTANCE, PUS_SERVICE, PUS_SUBSERVICE, None, None, True),
    TcPacketArgs(APID, SEQ_COUNT_OR_NAME, 2, AckFlag.ACCEPTANCE, PUS_SERVICE, PUS_SUBSERVICE, TC_SOURCE, None, True),
    TcPacketArgs(APID, SEQ_COUNT_OR_NAME, 2, AckFlag.ACCEPTANCE | AckFlag.COMPLETION, PUS_SERVICE, PUS_SUBSERVICE, TC_SOURCE, DATA, True),
])
def test_tc_packet_create(args):
    args_to_pass = {k: v for k, v in args._asdict().items() if v is not None}

    packet = PusTcPacket.create(**args_to_pass)
    assert packet.name == args.name
    assert packet.secondary_header.pus_version == args.pus_version
    assert packet.secondary_header.ack_flags == args.ack_flags
    assert packet.secondary_header.service_type == args.service_type
    assert packet.secondary_header.service_subtype == args.service_subtype
    assert packet.secondary_header.source == args.source


@pytest.mark.parametrize("args, length", [
    (TcPacketArgs(APID, SEQ_COUNT_OR_NAME, None, AckFlag.ACCEPTANCE, PUS_SERVICE, PUS_SUBSERVICE, None, None, False), 9),
    (TcPacketArgs(APID, SEQ_COUNT_OR_NAME, None, AckFlag.ACCEPTANCE, PUS_SERVICE, PUS_SUBSERVICE, None, b'', True), 11),
    (TcPacketArgs(APID, SEQ_COUNT_OR_NAME, None, AckFlag.ACCEPTANCE, PUS_SERVICE, PUS_SUBSERVICE, TC_SOURCE, b'', False), 11),
    (TcPacketArgs(APID, SEQ_COUNT_OR_NAME, None, AckFlag.ACCEPTANCE, PUS_SERVICE, PUS_SUBSERVICE, TC_SOURCE, b'', True), 13),
    (TcPacketArgs(APID, SEQ_COUNT_OR_NAME, None, AckFlag.ACCEPTANCE, PUS_SERVICE, PUS_SUBSERVICE, TC_SOURCE, DATA, False), 15),
    (TcPacketArgs(APID, SEQ_COUNT_OR_NAME, None, AckFlag.ACCEPTANCE, PUS_SERVICE, PUS_SUBSERVICE, TC_SOURCE, DATA, True), 17),
])
def test_tc_packet_length(args, length):
    args_to_pass = {k: v for k, v in args._asdict().items() if v is not None}
    packet = PusTcPacket.create(**args_to_pass)
    assert len(packet) == length


@pytest.mark.parametrize("args, binary", [
    (TcPacketArgs(APID, SEQ_COUNT_OR_NAME, None, AckFlag.ACCEPTANCE, PUS_SERVICE, PUS_SUBSERVICE, None, b'', False), bytes.fromhex('1810c0500002210801')),
    (TcPacketArgs(APID, SEQ_COUNT_OR_NAME, None, AckFlag.ACCEPTANCE, PUS_SERVICE, PUS_SUBSERVICE, None, b'', True), bytes.fromhex('1810c0500004210801bbc9')),
    (TcPacketArgs(APID, SEQ_COUNT_OR_NAME, None, AckFlag.ACCEPTANCE, PUS_SERVICE, PUS_SUBSERVICE, TC_SOURCE, b'', False), bytes.fromhex('1810c05000042108012021')),
    (TcPacketArgs(APID, SEQ_COUNT_OR_NAME, None, AckFlag.ACCEPTANCE, PUS_SERVICE, PUS_SUBSERVICE, TC_SOURCE, b'', True), bytes.fromhex('1810c050000621080120213377')),
    (TcPacketArgs(APID, SEQ_COUNT_OR_NAME, None, AckFlag.ACCEPTANCE, PUS_SERVICE, PUS_SUBSERVICE, TC_SOURCE, DATA, False), bytes.fromhex('1810c05000082108012021deadbeef')),
    (TcPacketArgs(APID, SEQ_COUNT_OR_NAME, None, AckFlag.ACCEPTANCE, PUS_SERVICE, PUS_SUBSERVICE, TC_SOURCE, DATA, True), bytes.fromhex('1810c050000a2108012021deadbeefc984')),
])
def test_tc_packet_serialize(args, binary):
    args_to_pass = {k: v for k, v in args._asdict().items() if v is not None}
    packet = PusTcPacket.create(**args_to_pass)
    buffer = packet.serialize()
    assert len(packet) == len(buffer)
    assert len(buffer) == len(binary)
    assert buffer == binary
    assert bytes(packet) == binary


@pytest.mark.parametrize("args, binary", [
    (TcPacketArgs(APID, SEQ_COUNT_OR_NAME, None, AckFlag.ACCEPTANCE, PUS_SERVICE, PUS_SUBSERVICE, None, b'', False), bytes.fromhex('1810c0500002210801')),
    (TcPacketArgs(APID, SEQ_COUNT_OR_NAME, None, AckFlag.ACCEPTANCE, PUS_SERVICE, PUS_SUBSERVICE, None, b'', True), bytes.fromhex('1810c0500004210801bbc9')),
    (TcPacketArgs(APID, SEQ_COUNT_OR_NAME, None, AckFlag.ACCEPTANCE, PUS_SERVICE, PUS_SUBSERVICE, TC_SOURCE, b'', False), bytes.fromhex('1810c05000042108012021')),
    (TcPacketArgs(APID, SEQ_COUNT_OR_NAME, None, AckFlag.ACCEPTANCE, PUS_SERVICE, PUS_SUBSERVICE, TC_SOURCE, b'', True), bytes.fromhex('1810c050000621080120213377')),
    (TcPacketArgs(APID, SEQ_COUNT_OR_NAME, None, AckFlag.ACCEPTANCE, PUS_SERVICE, PUS_SUBSERVICE, TC_SOURCE, DATA, False), bytes.fromhex('1810c05000082108012021deadbeef')),
    (TcPacketArgs(APID, SEQ_COUNT_OR_NAME, None, AckFlag.ACCEPTANCE, PUS_SERVICE, PUS_SUBSERVICE, TC_SOURCE, DATA, True), bytes.fromhex('1810c050000a2108012021deadbeefc984')),
])
def test_tc_packet_deserialize(args, binary):
    packet = PusTcPacket.deserialize(binary, has_source_field=True if args.source else False, has_pec=True if args.has_pec else False)
    assert packet.apid == args.apid
    assert packet.name == args.name
    assert packet.secondary_header.pus_version == (args.pus_version if args.pus_version else 2)
    assert packet.secondary_header.ack_flags == args.ack_flags
    assert packet.service == args.service_type
    assert packet.subservice == args.service_subtype
    assert packet.source == args.source
    assert packet.app_data == args.data
    assert packet.has_pec == args.has_pec

    buffer = packet.serialize()
    assert len(buffer) == len(binary)
    assert buffer == binary


PUS_SERVICE = 130
PUS_SUBSERVICE = 4
MSG_TYPE_COUNTER = 0x1314
TM_DESTINATION = 0x2021
TIME = CucTime(100, 10000, 4, 2)
DATA = bytes.fromhex('DEADBEEF')

TmPacketArgs = namedtuple('TmPacketArgs', ['apid', 'seq_count', 'pus_version', 'spacecraft_time_ref_status', 'service_type', 'service_subtype', 'msg_type_counter', 'destination', 'time', 'data', 'has_pec'])


@pytest.mark.parametrize("args", [
    TmPacketArgs(APID, SEQ_COUNT_OR_NAME, 1, None, PUS_SERVICE, PUS_SUBSERVICE, None, None, TIME, b'', True),
    TmPacketArgs(APID, SEQ_COUNT_OR_NAME, 2, 1, PUS_SERVICE, PUS_SUBSERVICE, MSG_TYPE_COUNTER, TM_DESTINATION, TIME, DATA, True),
])
def test_tm_packet_create(args):
    args_to_pass = {k: v for k, v in args._asdict().items() if v is not None}

    packet = PusTmPacket.create(**args_to_pass)
    assert packet.seq_count == args.seq_count
    assert packet.secondary_header.pus_version == args.pus_version
    assert packet.secondary_header.spacecraft_time_ref_status == (args.spacecraft_time_ref_status if args.spacecraft_time_ref_status else 0)
    assert packet.secondary_header.service_type == args.service_type
    assert packet.secondary_header.service_subtype == args.service_subtype
    assert packet.secondary_header.msg_type_counter == args.msg_type_counter
    assert packet.secondary_header.destination == args.destination
    assert packet.secondary_header.time == args.time
    assert packet.source_data == args.data


@pytest.mark.parametrize("args, length", [
    (TmPacketArgs(APID, SEQ_COUNT_OR_NAME, None, None, PUS_SERVICE, PUS_SUBSERVICE, None, None, TIME, None, False), 16),
    (TmPacketArgs(APID, SEQ_COUNT_OR_NAME, None, None, PUS_SERVICE, PUS_SUBSERVICE, MSG_TYPE_COUNTER, None, TIME, None, False), 18),
    (TmPacketArgs(APID, SEQ_COUNT_OR_NAME, None, None, PUS_SERVICE, PUS_SUBSERVICE, MSG_TYPE_COUNTER, TM_DESTINATION, TIME, None, False), 20),
    (TmPacketArgs(APID, SEQ_COUNT_OR_NAME, None, None, PUS_SERVICE, PUS_SUBSERVICE, MSG_TYPE_COUNTER, TM_DESTINATION, TIME, DATA, False), 24),
    (TmPacketArgs(APID, SEQ_COUNT_OR_NAME, None, None, PUS_SERVICE, PUS_SUBSERVICE, MSG_TYPE_COUNTER, TM_DESTINATION, TIME, DATA, True), 26),
])
def test_tm_packet_length(args, length):
    args_to_pass = {k: v for k, v in args._asdict().items() if v is not None}
    packet = PusTmPacket.create(**args_to_pass)
    assert len(packet) == length


@pytest.mark.parametrize("args, binary", [
    (TmPacketArgs(APID, SEQ_COUNT_OR_NAME, None, None, PUS_SERVICE, PUS_SUBSERVICE, None, None, TIME, None, False), bytes.fromhex('0810c0500009208204') + bytes(TIME)),
    (TmPacketArgs(APID, SEQ_COUNT_OR_NAME, None, None, PUS_SERVICE, PUS_SUBSERVICE, MSG_TYPE_COUNTER, None, TIME, None, False), bytes.fromhex('0810c050000b2082041314') + bytes(TIME)),
    (TmPacketArgs(APID, SEQ_COUNT_OR_NAME, None, 1, PUS_SERVICE, PUS_SUBSERVICE, MSG_TYPE_COUNTER, TM_DESTINATION, TIME, None, False), bytes.fromhex('0810c050000d21820413142021') + bytes(TIME)),
    (TmPacketArgs(APID, SEQ_COUNT_OR_NAME, None, 1, PUS_SERVICE, PUS_SUBSERVICE, MSG_TYPE_COUNTER, TM_DESTINATION, TIME, DATA, False), bytes.fromhex('0810c050001121820413142021') + bytes(TIME) + DATA),
    (TmPacketArgs(APID, SEQ_COUNT_OR_NAME, None, 1, PUS_SERVICE, PUS_SUBSERVICE, MSG_TYPE_COUNTER, TM_DESTINATION, TIME, DATA, True), bytes.fromhex('0810c050001321820413142021') + bytes(TIME) + DATA + bytes.fromhex('0483')),
])
def test_tm_packet_serialize(args, binary):
    args_to_pass = {k: v for k, v in args._asdict().items() if v is not None}
    packet = PusTmPacket.create(**args_to_pass)
    buffer = packet.serialize()
    assert len(packet) == len(buffer)
    assert len(buffer) == len(binary)
    assert buffer == binary
    assert bytes(packet) == binary


@pytest.mark.parametrize("args, binary", [
    (TmPacketArgs(APID, SEQ_COUNT_OR_NAME, None, None, PUS_SERVICE, PUS_SUBSERVICE, None, None, TIME, b'', False), bytes.fromhex('0810c0500009208204') + bytes(TIME)),
    (TmPacketArgs(APID, SEQ_COUNT_OR_NAME, None, None, PUS_SERVICE, PUS_SUBSERVICE, MSG_TYPE_COUNTER, None, TIME, b'', False), bytes.fromhex('0810c050000b2082041314') + bytes(TIME)),
    (TmPacketArgs(APID, SEQ_COUNT_OR_NAME, None, 1, PUS_SERVICE, PUS_SUBSERVICE, MSG_TYPE_COUNTER, TM_DESTINATION, TIME, b'', False), bytes.fromhex('0810c050000d21820413142021') + bytes(TIME)),
    (TmPacketArgs(APID, SEQ_COUNT_OR_NAME, None, 1, PUS_SERVICE, PUS_SUBSERVICE, MSG_TYPE_COUNTER, TM_DESTINATION, TIME, DATA, False), bytes.fromhex('0810c050001121820413142021') + bytes(TIME) + DATA),
    (TmPacketArgs(APID, SEQ_COUNT_OR_NAME, None, 1, PUS_SERVICE, PUS_SUBSERVICE, MSG_TYPE_COUNTER, TM_DESTINATION, TIME, DATA, True), bytes.fromhex('0810c050001321820413142021') + bytes(TIME) + DATA + bytes.fromhex('0483')),
])
def test_tm_packet_deserialize(args, binary):
    packet = PusTmPacket.deserialize(binary, has_type_counter_field=True if args.msg_type_counter else False, has_destination_field=True if args.destination else False, cuc_time=TIME, has_pec=True if args.has_pec else False)
    assert packet.apid == args.apid
    assert packet.seq_count == args.seq_count
    assert packet.secondary_header.pus_version == (args.pus_version if args.pus_version else 2)
    assert packet.secondary_header.spacecraft_time_ref_status == (args.spacecraft_time_ref_status if args.spacecraft_time_ref_status else 0)
    assert packet.service == args.service_type
    assert packet.subservice == args.service_subtype
    assert packet.counter == args.msg_type_counter
    assert packet.destination == args.destination
    assert packet.time == args.time
    assert packet.source_data == args.data
    assert len(packet.source_data) == len(args.data)
    assert packet.has_pec == args.has_pec

    buffer = packet.serialize()
    assert len(buffer) == len(binary)
    assert buffer == binary
