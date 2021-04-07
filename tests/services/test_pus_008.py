from collections import namedtuple

import pytest

from puslib.ident import PusIdent
from puslib.packet import PusTcPacket, AckFlag
from puslib.parameter import UInt16Parameter, UInt32Parameter, UInt64Parameter
from puslib.services import RequestVerification, PusService8
from puslib.streams.buffer import QueuedOutput

FunctionTestArgs = namedtuple('FunctionTestArgs', ['function', 'fid', 'function_args', 'tc_app_data', 'expected_pus1_subservice'])


def function_with_no_args():
    return True


def function_with_one_arg(arg1):
    assert arg1 == 1
    return True


def function_with_two_args(arg1, arg2):
    assert arg1 == 1
    assert arg2 == 2
    return True


@pytest.mark.parametrize("args", [
    FunctionTestArgs(function_with_no_args, 0, None, bytes.fromhex(""), 2),  # Invalid app data
    FunctionTestArgs(function_with_no_args, 0, None, bytes.fromhex("0000"), 1),
    FunctionTestArgs(function_with_no_args, 0, None, bytes.fromhex("0001"), 2),  # Unsupported FID
    FunctionTestArgs(function_with_no_args, 0, None, bytes.fromhex("0000deadbeef"), 2),  # Too much app data
    FunctionTestArgs(function_with_one_arg, 0, [UInt32Parameter], bytes.fromhex("000000000001"), 1),
    FunctionTestArgs(function_with_two_args, 0, [UInt16Parameter, UInt64Parameter], bytes.fromhex("000000010000000000000002"), 1),
    FunctionTestArgs(function_with_two_args, 0, [UInt16Parameter, UInt64Parameter], bytes.fromhex("00000001"), 2),  # Too little app data
    FunctionTestArgs(function_with_two_args, 0, [UInt16Parameter, UInt64Parameter], bytes.fromhex("000000010000000000000002deadbeef"), 2),  # Too much app data
])
def test_function_without_arguments(args):
    ident = PusIdent(apid=10)
    tm_stream = QueuedOutput()
    pus_service_1 = RequestVerification(ident, tm_stream)
    pus_service_8 = PusService8(ident, pus_service_1)
    pus_service_8.add(args.function, fid=args.fid, args=args.function_args)

    packet = PusTcPacket.create(apid=ident.apid, name=0, ack_flags=AckFlag.ACCEPTANCE, service_type=8, service_subtype=1, data=args.tc_app_data)
    pus_service_8.enqueue(packet)
    pus_service_8.process()
    assert tm_stream.size == 1
    report = tm_stream.get()
    assert report.service == 1
    assert report.subservice == args.expected_pus1_subservice
