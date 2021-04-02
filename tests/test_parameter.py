import struct
from collections import namedtuple

import pytest

from puslib import parameter

ParamTestArgs = namedtuple('ParamTestArgs', ['param_class', 'pus_param_type', 'python_type', 'init_value', 'new_value', 'value_size', 'too_small_value', 'too_large_value'])


@pytest.mark.parametrize("args", [
    ParamTestArgs(parameter.UInt8Parameter, parameter.PacketFieldType.UInt, int, 1, 2, 1, -1, 2 ** 8),
    ParamTestArgs(parameter.UInt16Parameter, parameter.PacketFieldType.UInt, int, 1, 2, 2, -1, 2 ** 16),
    ParamTestArgs(parameter.UInt32Parameter, parameter.PacketFieldType.UInt, int, 1, 2, 4, -1, 2 ** 32),
    ParamTestArgs(parameter.UInt64Parameter, parameter.PacketFieldType.UInt, int, 1, 2, 8, -1, 2 ** 64),
    ParamTestArgs(parameter.Int8Parameter, parameter.PacketFieldType.Int, int, -1, 2, 1, -2 ** 7 - 1, 2 ** 7),
    ParamTestArgs(parameter.Int16Parameter, parameter.PacketFieldType.Int, int, -1, 2, 2, -2 ** 15 - 1, 2 ** 15),
    ParamTestArgs(parameter.Int32Parameter, parameter.PacketFieldType.Int, int, -1, 2, 4, -2 ** 31 - 1, 2 ** 31),
    ParamTestArgs(parameter.Int64Parameter, parameter.PacketFieldType.Int, int, -1, 2, 8, -2 ** 63 - 1, 2 ** 63),
    ParamTestArgs(parameter.Real32Parameter, parameter.PacketFieldType.Real, float, -1.5, 2.5, 4, None, None),
    ParamTestArgs(parameter.Real64Parameter, parameter.PacketFieldType.Real, float, -1.5, 2.5, 8, None, None),
])
def test_numeric_parameter(args):
    param = args.param_class(args.init_value)
    assert param.value == args.init_value
    assert param.type == args.pus_param_type
    assert type(param.value) == args.python_type
    assert param.size == args.value_size
    if param.type == parameter.PacketFieldType.UInt:
        struct.pack(param.format, param.value) == args.init_value.to_bytes(args.value_size, byteorder='big')
    elif param.type == parameter.PacketFieldType.Int:
        struct.pack(param.format, param.value) == args.init_value.to_bytes(args.value_size, byteorder='big', signed=True)
    elif param.type == parameter.PacketFieldType.Real:
        pass
    else:
        assert False, "Unknown conversion to bytes"
    param.value = args.new_value
    assert param.value == args.new_value
    if args.too_small_value:
        with pytest.raises(ValueError):
            param.value = args.too_small_value
    if args.too_large_value:
        with pytest.raises(ValueError):
            param.value = args.too_large_value
