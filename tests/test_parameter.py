import struct
from collections import namedtuple

import pytest

from puslib import parameter

NumericParamTestArgs = namedtuple('NumericParamTestArgs', ['param_class', 'pus_param_type', 'python_type', 'init_value', 'new_value', 'value_size', 'too_small_value', 'too_large_value'])


@pytest.mark.parametrize("args", [
    NumericParamTestArgs(parameter.BoolParameter, parameter.PacketFieldType.BOOLEAN, bool, False, True, 1, None, None),
    NumericParamTestArgs(parameter.UInt8Parameter, parameter.PacketFieldType.UINT, int, 1, 2, 1, -1, 2 ** 8),
    NumericParamTestArgs(parameter.UInt16Parameter, parameter.PacketFieldType.UINT, int, 1, 2, 2, -1, 2 ** 16),
    NumericParamTestArgs(parameter.UInt32Parameter, parameter.PacketFieldType.UINT, int, 1, 2, 4, -1, 2 ** 32),
    NumericParamTestArgs(parameter.UInt64Parameter, parameter.PacketFieldType.UINT, int, 1, 2, 8, -1, 2 ** 64),
    NumericParamTestArgs(parameter.Int8Parameter, parameter.PacketFieldType.INT, int, -1, 2, 1, -2 ** 7 - 1, 2 ** 7),
    NumericParamTestArgs(parameter.Int16Parameter, parameter.PacketFieldType.INT, int, -1, 2, 2, -2 ** 15 - 1, 2 ** 15),
    NumericParamTestArgs(parameter.Int32Parameter, parameter.PacketFieldType.INT, int, -1, 2, 4, -2 ** 31 - 1, 2 ** 31),
    NumericParamTestArgs(parameter.Int64Parameter, parameter.PacketFieldType.INT, int, -1, 2, 8, -2 ** 63 - 1, 2 ** 63),
    NumericParamTestArgs(parameter.Real32Parameter, parameter.PacketFieldType.REAL, float, -1.5, 2.5, 4, None, None),
    NumericParamTestArgs(parameter.Real64Parameter, parameter.PacketFieldType.REAL, float, -1.5, 2.5, 8, None, None),
])
def test_numeric_parameter(args):
    param = args.param_class(args.init_value)
    assert param.value == args.init_value
    assert param.ptc == args.pus_param_type
    assert isinstance(param.value, args.python_type)
    assert param.size == args.value_size
    param_bytes = param.to_bytes()
    assert len(param_bytes) == args.value_size
    if param.ptc in (parameter.PacketFieldType.UINT, parameter.PacketFieldType.BOOLEAN):
        assert struct.pack(param.format, param.value) == args.init_value.to_bytes(args.value_size, byteorder='big')
        assert int.from_bytes(param_bytes, byteorder='big') == args.param_class.from_bytes(param_bytes)
    elif param.ptc == parameter.PacketFieldType.INT:
        assert struct.pack(param.format, param.value) == args.init_value.to_bytes(args.value_size, byteorder='big', signed=True)
        assert int.from_bytes(param_bytes, byteorder='big', signed=True) == args.param_class.from_bytes(param_bytes)
    elif param.ptc == parameter.PacketFieldType.REAL:
        assert args.param_class.from_bytes(param_bytes) == param.value
    else:
        assert False, "Unknown conversion to bytes"
    param.value = args.new_value
    assert param.value == args.new_value
    if args.too_small_value:
        with pytest.raises(ValueError):
            param.value = args.too_small_value
        param.value = args.too_small_value + 1
    if args.too_large_value:
        with pytest.raises(ValueError):
            param.value = args.too_large_value
        param.value = args.too_large_value - 1


EnumParamTestArgs = namedtuple('NumericParamTestArgs', ['init_value', 'new_value', 'bitsize', 'value_size', 'too_small_value', 'too_large_value'])


@pytest.mark.parametrize("args", [
    EnumParamTestArgs(0, 1, 4, 1, -1, 2 ** 4),
    EnumParamTestArgs(0, 1, 8, 1, -1, 2 ** 8),
    EnumParamTestArgs(0, 1, 12, 2, -1, 2 ** 12),
    EnumParamTestArgs(0, 1, 16, 2, -1, 2 ** 16),
    EnumParamTestArgs(0, 1, 24, 4, -1, 2 ** 24),
    EnumParamTestArgs(0, 1, 32, 4, -1, 2 ** 32),
    EnumParamTestArgs(0, 1, 48, 8, -1, 2 ** 48),
    EnumParamTestArgs(0, 1, 64, 8, -1, 2 ** 64),
])
def test_enumerate_parameter(args):
    param = parameter.EnumParameter(args.init_value, args.bitsize)
    assert param.value == args.init_value
    assert param.ptc == parameter.PacketFieldType.ENUMERATED
    assert isinstance(param.value, int)
    assert param.size == args.value_size
    param_bytes = param.to_bytes()
    assert len(param_bytes) == args.value_size
    assert struct.pack(param.format, param.value) == args.init_value.to_bytes(args.value_size, byteorder='big')
    assert int.from_bytes(param_bytes, byteorder='big') == parameter.EnumParameter.from_bytes(param_bytes, param.size)
    param.value = args.new_value
    assert param.value == args.new_value
    with pytest.raises(ValueError):
        param.value = args.too_small_value
    param.value = args.too_small_value + 1
    with pytest.raises(ValueError):
        param.value = args.too_large_value
    param.value = args.too_large_value - 1
