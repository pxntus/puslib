
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
    _value_type = None

    def __init__(self, init_value=None):
        if init_value:
            self._validate(init_value)
        self._value = init_value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._validate(new_value)
        self._value = new_value

    @property
    def format(self):
        raise NotImplementedError

    @property
    def size(self):
        return struct.calcsize(self.format)

    def _validate(self, value):
        raise NotImplementedError

    @classmethod
    def type(cls):
        return cls._value_type


class BoolParameter(Parameter):
    _value_type = PacketFieldType.Boolean
    _fmt = '>?'
    _struct = struct.Struct(_fmt)

    def _validate(self, value):
        if not isinstance(value, bool):
            raise TypeError("Boolean expected")

    @property
    def format(self):
        return self._fmt

    @classmethod
    def from_bytes(cls, bytes):
        val = cls._struct.unpack(bytes)
        return cls(val)


class _UnsignedIntegerParameter(Parameter):
    _value_type = PacketFieldType.UInt

    def _validate(self, value):
        if not isinstance(value, int):
            raise TypeError("Integer expected")
        if not (0 <= value <= (2 ** (self.size * 8) - 1)):
            raise ValueError


class UInt8Parameter(_UnsignedIntegerParameter):
    @property
    def format(self):
        return 'B'

    @classmethod
    def from_bytes(cls, bytes):
        val = int.from_bytes(bytes[0], byteorder='big')
        return cls(val)


class UInt16Parameter(_UnsignedIntegerParameter):
    @property
    def format(self):
        return '>H'

    @classmethod
    def from_bytes(cls, bytes):
        val = int.from_bytes(bytes[:2], byteorder='big')
        return cls(val)


class UInt32Parameter(_UnsignedIntegerParameter):
    @property
    def format(self):
        return '>I'

    @classmethod
    def from_bytes(cls, bytes):
        val = int.from_bytes(bytes[:4], byteorder='big')
        return cls(val)


class UInt64Parameter(_UnsignedIntegerParameter):
    @property
    def format(self):
        return '>Q'

    @classmethod
    def from_bytes(cls, bytes):
        val = int.from_bytes(bytes[:8], byteorder='big')
        return cls(val)


class _SignedIntegerParameter(Parameter):
    _value_type = PacketFieldType.Int

    def _validate(self, value):
        if not isinstance(value, int):
            raise TypeError("Integer expected")
        if not ((-2 ** (self.size * 8 - 1)) <= value <= (2 ** (self.size * 8 - 1) - 1)):
            raise ValueError


class Int8Parameter(_SignedIntegerParameter):
    @property
    def format(self):
        return 'b'

    @classmethod
    def from_bytes(cls, bytes):
        val = int.from_bytes(bytes[0], byteorder='big', signed=True)
        return cls(val)


class Int16Parameter(_SignedIntegerParameter):
    @property
    def format(self):
        return '>h'

    @classmethod
    def from_bytes(cls, bytes):
        val = int.from_bytes(bytes[:2], byteorder='big', signed=True)
        return cls(val)


class Int32Parameter(_SignedIntegerParameter):
    @property
    def format(self):
        return '>i'

    @classmethod
    def from_bytes(cls, bytes):
        val = int.from_bytes(bytes[:4], byteorder='big', signed=True)
        return cls(val)


class Int64Parameter(_SignedIntegerParameter):
    @property
    def format(self):
        return '>q'

    @classmethod
    def from_bytes(cls, bytes):
        val = int.from_bytes(bytes[:8], byteorder='big', signed=True)
        return cls(val)


class _RealParameter(Parameter):
    _value_type = PacketFieldType.Real

    def _validate(self, value):
        if not isinstance(value, float):
            raise TypeError("Float expected")


class Real32Parameter(_RealParameter):
    _fmt = '>f'
    _struct = struct.Struct(_fmt)

    @property
    def format(self):
        return self._fmt

    @classmethod
    def from_bytes(cls, bytes):
        val = cls._struct.unpack(bytes)
        return cls(val)


class Real64Parameter(_RealParameter):
    _fmt = '>d'
    _struct = struct.Struct(_fmt)

    @property
    def format(self):
        return self._fmt

    @classmethod
    def from_bytes(cls, bytes):
        val = cls._struct.unpack(bytes)
        return cls(val)


class OctetStringParameter(Parameter):
    _value_type = PacketFieldType.OctetString

    def _validate(self, value):
        if not isinstance(value, (bytes, bytearray)):
            raise TypeError("Bytes or bytearray expected")

    @property
    def format(self):
        return len(self.value) + 's'

    @classmethod
    def from_bytes(cls, bytes):
        raise NotImplementedError


class AbsoluteTimeParameter(Parameter):
    _value_type = PacketFieldType.AbsoluteTime

    def _validate(self, value):
        if not isinstance(value, CucTime):
            raise TypeError("CucTime expected")

    @property
    def format(self):
        return len(self.value) + 's'

    @classmethod
    def from_bytes(cls, bytes):
        raise NotImplementedError


class RelativeTimeParameter(AbsoluteTimeParameter):
    _value_type = PacketFieldType.RelativeTime


class PacketParameter(Parameter):
    _value_type = PacketFieldType.Packet

    def _validate(self, value):
        if not isinstance(value, PusTcPacket):
            raise TypeError("PusTcPacket expected")

    @property
    def format(self):
        return len(self.value) + 's'

    @classmethod
    def from_bytes(cls, bytes):
        raise NotImplementedError
