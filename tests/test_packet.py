from collections import namedtuple

import pytest

from puslib.packet import CcsdsSpacePacket
from puslib.packet import PusTcPacket
from puslib.packet import PusTmPacket
from puslib.packet import PacketType
from puslib.packet import AckFlag

CcsdsPacketArgs = namedtuple('CcsdsPacketArgs', ['packet_version_number', 'packet_type', 'secondary_header_flag', 'apid', 'seq_flags', 'seq_count_or_name', 'data', 'has_pec'])


@pytest.mark.parametrize("args", [
    CcsdsPacketArgs(None, PacketType.TC, None, 10, None, 37, None, True),
    CcsdsPacketArgs(None, PacketType.TC, None, 10, None, 37, None, False),
    CcsdsPacketArgs(0, PacketType.TM, True, 10, 0b11, 37, bytes([0x01, 0x02, 0x03, 0x04]), True),
    CcsdsPacketArgs(0, PacketType.TM, False, 10, 0b11, 37, bytes([0x01, 0x02, 0x03, 0x04]), False),
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
    TcPacketArgs(10, 20, None, AckFlag.ACCEPTANCE, 8, 1, None, None, True),
    TcPacketArgs(10, 20, 0, AckFlag.ACCEPTANCE, 8, 1, 155, None, True),
    TcPacketArgs(10, 20, 0, AckFlag.ACCEPTANCE | AckFlag.COMPLETION, 8, 1, 155, bytes([0x01, 0x02]), True),
])
def test_tc_packet_create(args):
    args_to_pass = {k: v for k, v in args._asdict().items() if v is not None}

    packet = PusTcPacket.create(**args_to_pass)
    packet.name == args.name
    packet.secondary_header.pus_version == args.pus_version
    packet.secondary_header.ack_flags == args.ack_flags
    packet.secondary_header.service_type == args.service_type
    packet.secondary_header.service_subtype == args.service_subtype
    packet.secondary_header.source == args.source


@pytest.mark.parametrize("args, length", [
    (TcPacketArgs(10, 20, None, AckFlag.ACCEPTANCE, 8, 1, None, None, False), 9),
    (TcPacketArgs(10, 20, None, AckFlag.ACCEPTANCE, 8, 1, None, None, True), 11),
    (TcPacketArgs(10, 20, None, AckFlag.ACCEPTANCE, 8, 1, 155, None, False), 11),
    (TcPacketArgs(10, 20, None, AckFlag.ACCEPTANCE, 8, 1, 155, None, True), 13),
    (TcPacketArgs(10, 20, None, AckFlag.ACCEPTANCE, 8, 1, 155, bytes([0x01, 0x02]), False), 13),
    (TcPacketArgs(10, 20, None, AckFlag.ACCEPTANCE, 8, 1, 155, bytes([0x01, 0x02]), True), 15),
])
def test_tc_packet_length(args, length):
    args_to_pass = {k: v for k, v in args._asdict().items() if v is not None}
    packet = PusTcPacket.create(**args_to_pass)
    len(packet)


def test_tc_packet_serialize():
    raise NotImplementedError


def test_tc_packet_deserialize():
    raise NotImplementedError


def test_tm_packet_create():
    raise NotImplementedError


def test_tm_packet_length():
    raise NotImplementedError


def test_tm_packet_serialize():
    raise NotImplementedError


def test_tm_packet_deserialize():
    raise NotImplementedError
