
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
        self._events = []

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        if self._value == new_value:
            return
        self._validate(new_value)
        old_value = self._value
        self._value = new_value
        if self._events:
            for event in self._events:
                event(old_value=old_value, new_value=self._value)

    @property
    def format(self):
        raise NotImplementedError

    @property
    def size(self):
        return struct.calcsize(self.format)

    def subscribe(self, event_handler):
        self._events.append(event_handler)

    def to_bytes(self):
        return struct.pack(self.format, self.value)

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


class _IntegerParameter(Parameter):
    _value_size = None
    _fmt = None
    _signed = None

    @property
    def size(self):
        return self._value_size

    @property
    def format(self):
        return self._fmt

    def to_bytes(self):
        return self.value.to_bytes(self._value_size, byteorder='big', signed=self._signed)

    @classmethod
    def from_bytes(cls, bytes):
        val = int.from_bytes(bytes[:cls._value_size], byteorder='big', signed=cls._signed)
        return cls(val)


class _UnsignedIntegerParameter(_IntegerParameter):
    _value_type = PacketFieldType.UInt
    _signed = False

    def _validate(self, value):
        if not isinstance(value, int):
            raise TypeError("Integer expected")
        if not (0 <= value <= (2 ** (self._value_size * 8) - 1)):
            raise ValueError


class UInt8Parameter(_UnsignedIntegerParameter):
    _value_size = 1
    _fmt = 'B'


class UInt16Parameter(_UnsignedIntegerParameter):
    _value_size = 2
    _fmt = '>H'


class UInt32Parameter(_UnsignedIntegerParameter):
    _value_size = 4
    _fmt = '>I'


class UInt64Parameter(_UnsignedIntegerParameter):
    _value_size = 8
    _fmt = '>Q'


class _SignedIntegerParameter(_IntegerParameter):
    _value_type = PacketFieldType.Int
    _signed = True

    def _validate(self, value):
        if not isinstance(value, int):
            raise TypeError("Integer expected")
        if not ((-2 ** (self.size * 8 - 1)) <= value <= (2 ** (self._value_size * 8 - 1) - 1)):
            raise ValueError


class Int8Parameter(_SignedIntegerParameter):
    _value_size = 1
    _fmt = 'b'


class Int16Parameter(_SignedIntegerParameter):
    _value_size = 2
    _fmt = '>h'


class Int32Parameter(_SignedIntegerParameter):
    _value_size = 4
    _fmt = '>i'


class Int64Parameter(_SignedIntegerParameter):
    _value_size = 8
    _fmt = '>q'


class _RealParameter(Parameter):
    _value_type = PacketFieldType.Real
    _fmt = None

    @property
    def format(self):
        return self._fmt

    def _validate(self, value):
        if not isinstance(value, float):
            raise TypeError("Float expected")

    @classmethod
    def from_bytes(cls, bytes):
        val = cls._struct.unpack(bytes)
        return cls(val)


class Real32Parameter(_RealParameter):
    _fmt = '>f'
    _struct = struct.Struct(_fmt)


class Real64Parameter(_RealParameter):
    _fmt = '>d'
    _struct = struct.Struct(_fmt)


class OctetStringParameter(Parameter):
    _value_type = PacketFieldType.OctetString

    def _validate(self, value):
        if not isinstance(value, (bytes, bytearray)):
            raise TypeError("Bytes or bytearray expected")

    @property
    def format(self, length_type_size):
        return f"{length_type_size + len(self.value)}s"

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
        return f"{len(self.value)}s"

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
        return f"{len(self.value)}s"

    @classmethod
    def from_bytes(cls, bytes):
        raise NotImplementedError
