
import struct
from enum import IntEnum

from .time import CucTime
from .packet import PusTcPacket


class PacketFieldType(IntEnum):
    Boolean = 1
    Enumerated = 2
    UInt = 3
    Int = 4
    Real = 5
    BitString = 6
    OctetString = 7
    String = 8
    AbsoluteTime = 9
    RelativeTime = 10
    Deducted = 11
    Packet = 12


class Parameter:
    def __init__(self, value_type, init_value=None):
        if init_value:
            self._validate(init_value)
        self._value = init_value
        self._value_type = value_type

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._validate(new_value)
        self._value = new_value

    @property
    def type(self):
        return self._value_type

    @property
    def format(self):
        raise NotImplementedError

    @property
    def size(self):
        return struct.calcsize(self.format)

    def _validate(self, value):
        raise NotImplementedError


class BoolParameter(Parameter):
    def __init__(self, init_value=None):
        super().__init__(PacketFieldType.Boolean, init_value)

    def _validate(self, value):
        if not isinstance(value, bool):
            raise TypeError("Boolean expected")

    @property
    def format(self):
        return '?'


class _UnsignedIntegerParameter(Parameter):
    def __init__(self, init_value=None):
        super().__init__(PacketFieldType.UInt, init_value)

    def _validate(self, value):
        if not isinstance(value, int):
            raise TypeError("Integer expected")
        if not (0 <= value <= (2 ** (self.size * 8) - 1)):
            raise ValueError


class UInt8Parameter(_UnsignedIntegerParameter):
    @property
    def format(self):
        return 'B'


class UInt16Parameter(_UnsignedIntegerParameter):
    @property
    def format(self):
        return '>H'


class UInt32Parameter(_UnsignedIntegerParameter):
    @property
    def format(self):
        return '>I'


class UInt64Parameter(_UnsignedIntegerParameter):
    @property
    def format(self):
        return '>Q'


class _SignedIntegerParameter(Parameter):
    def __init__(self, init_value=None):
        super().__init__(PacketFieldType.Int, init_value)

    def _validate(self, value):
        if not isinstance(value, int):
            raise TypeError("Integer expected")
        if not ((-2 ** (self.size * 8 - 1)) <= value <= (2 ** (self.size * 8 - 1) - 1)):
            raise ValueError


class Int8Parameter(_SignedIntegerParameter):
    @property
    def format(self):
        return 'b'


class Int16Parameter(_SignedIntegerParameter):
    @property
    def format(self):
        return '>h'


class Int32Parameter(_SignedIntegerParameter):
    @property
    def format(self):
        return '>i'


class Int64Parameter(_SignedIntegerParameter):
    @property
    def format(self):
        return '>q'


class _RealParameter(Parameter):
    def __init__(self, init_value=None):
        super().__init__(PacketFieldType.Real, init_value)

    def _validate(self, value):
        if not isinstance(value, float):
            raise TypeError("Float expected")


class Real32Parameter(_RealParameter):
    @property
    def format(self):
        return '>f'


class Real64Parameter(_RealParameter):
    @property
    def format(self):
        return '>d'


class OctetStringParameter(Parameter):
    def __init__(self, init_value=None):
        super().__init__(PacketFieldType.OctetString, init_value)

    def _validate(self, value):
        if not isinstance(value, (bytes, bytearray)):
            raise TypeError("Bytes or bytearray expected")

    @property
    def format(self):
        return len(self.value) + 's'


class AbsoluteTimeParameter(Parameter):
    def __init__(self, init_value=None):
        super().__init__(PacketFieldType.AbsoluteTime, init_value)

    def _validate(self, value):
        if not isinstance(value, CucTime):
            raise TypeError("CucTime expected")

    @property
    def format(self):
        return len(self.value) + 's'


class RelativeTimeParameter(AbsoluteTimeParameter):
    def __init__(self, init_value=None):
        super(Parameter, self).__init__(PacketFieldType.RelativeTime, init_value)


class PacketParameter(Parameter):
    def __init__(self, init_value=None):
        super().__init__(PacketFieldType.Packet, init_value)

    def _validate(self, value):
        if not isinstance(value, PusTcPacket):
            raise TypeError("PusTcPacket expected")

    @property
    def format(self):
        return len(self.value) + 's'
