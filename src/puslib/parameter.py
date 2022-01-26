
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


class _Parameter:
    _type_code = None

    def __init__(self, format_code, init_value=None):
        self._format_code = format_code
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
    def ptc(self):
        return self._type_code

    @property
    def pfc(self):
        return self._format_code

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


class BoolParameter(_Parameter):
    _type_code = PacketFieldType.Boolean
    _fmt = '>?'
    _struct = struct.Struct(_fmt)

    def __init__(self, init_value=False):
        super().__init__(format_code=8, init_value=init_value)

    @property
    def format(self):
        return self._fmt

    @property
    def size(self):
        return 1

    def _validate(self, value):
        if not isinstance(value, bool):
            raise TypeError("Boolean expected")

    @classmethod
    def from_bytes(cls, bytes):
        return cls._struct.unpack(bytes)[0]


class EnumParameter(_Parameter):
    _type_code = PacketFieldType.Enumerated

    def __init__(self, init_value=0, bitsize=8):
        super().__init__(format_code=bitsize, init_value=init_value)
        if not 1 <= bitsize <= 64:
            raise ValueError()
        self._format_code = bitsize
        value_size = bitsize // 8 + (1 if bitsize % 8 != 0 else 0)
        self._fmt = {1: '>B', 2: '>H', 3: '>I', 4: '>I'}.get(value_size, '>Q')

    @property
    def format(self):
        return self._fmt

    def _validate(self, value):
        if not isinstance(value, int):
            raise TypeError("Integer expected")
        if not (0 <= value <= (2 ** self._format_code - 1)):
            raise ValueError

    @classmethod
    def from_bytes(cls, bytes, bitsize):
        value_size = bitsize // 8 + (1 if bitsize % 8 != 0 else 0)
        return int.from_bytes(bytes[:value_size], byteorder='big')


class NumericParameter(_Parameter):
    _value_size = None
    _fmt = None

    @property
    def size(self):
        return self._value_size

    @property
    def format(self):
        return self._fmt


class _IntegerParameter(NumericParameter):
    _signed = None

    def to_bytes(self):
        return self.value.to_bytes(self._value_size, byteorder='big', signed=self._signed)

    @classmethod
    def from_bytes(cls, bytes):
        return int.from_bytes(bytes[:cls._value_size], byteorder='big', signed=cls._signed)


class _UnsignedIntegerParameter(_IntegerParameter):
    _type_code = PacketFieldType.UInt
    _signed = False

    def _validate(self, value):
        if not isinstance(value, int):
            raise TypeError("Integer expected")
        if not (0 <= value <= (2 ** (self._value_size * 8) - 1)):
            raise ValueError


class UInt8Parameter(_UnsignedIntegerParameter):
    _value_size = 1
    _fmt = 'B'

    def __init__(self, init_value=0):
        super().__init__(format_code=4, init_value=init_value)


class UInt16Parameter(_UnsignedIntegerParameter):
    _value_size = 2
    _fmt = '>H'

    def __init__(self, init_value=0):
        super().__init__(format_code=12, init_value=init_value)


class UInt32Parameter(_UnsignedIntegerParameter):
    _value_size = 4
    _fmt = '>I'

    def __init__(self, init_value=0):
        super().__init__(format_code=14, init_value=init_value)


class UInt64Parameter(_UnsignedIntegerParameter):
    _value_size = 8
    _fmt = '>Q'

    def __init__(self, init_value=0):
        super().__init__(format_code=16, init_value=init_value)


class _SignedIntegerParameter(_IntegerParameter):
    _type_code = PacketFieldType.Int
    _signed = True

    def _validate(self, value):
        if not isinstance(value, int):
            raise TypeError("Integer expected")
        if not ((-2 ** (self.size * 8 - 1)) <= value <= (2 ** (self._value_size * 8 - 1) - 1)):
            raise ValueError


class Int8Parameter(_SignedIntegerParameter):
    _value_size = 1
    _fmt = 'b'

    def __init__(self, init_value=0):
        super().__init__(format_code=4, init_value=init_value)


class Int16Parameter(_SignedIntegerParameter):
    _value_size = 2
    _fmt = '>h'

    def __init__(self, init_value=0):
        super().__init__(format_code=12, init_value=init_value)


class Int32Parameter(_SignedIntegerParameter):
    _value_size = 4
    _fmt = '>i'

    def __init__(self, init_value=0):
        super().__init__(format_code=14, init_value=init_value)


class Int64Parameter(_SignedIntegerParameter):
    _value_size = 8
    _fmt = '>q'

    def __init__(self, init_value=0):
        super().__init__(format_code=16, init_value=init_value)


class _RealParameter(NumericParameter):
    _type_code = PacketFieldType.Real
    _fmt = None

    def _validate(self, value):
        if not isinstance(value, float):
            raise TypeError("Float expected")

    @classmethod
    def from_bytes(cls, bytes):
        return cls._struct.unpack(bytes)[0]


class Real32Parameter(_RealParameter):
    _value_size = 4
    _fmt = '>f'
    _struct = struct.Struct(_fmt)

    def __init__(self, init_value=0):
        super().__init__(format_code=1, init_value=init_value)


class Real64Parameter(_RealParameter):
    _value_size = 8
    _fmt = '>d'
    _struct = struct.Struct(_fmt)

    def __init__(self, init_value=0):
        super().__init__(format_code=2, init_value=init_value)


class ArrayParameter(_Parameter):
    pass


class OctetStringParameter(ArrayParameter):
    _type_code = PacketFieldType.OctetString

    def __init__(self, init_value=None):
        super().__init__(format_code=0, init_value=init_value)

    @property
    def format(self, length_type):
        return f"{length_type.format + len(self.value)}s"

    @property
    def size(self):
        return len(self.value)

    def _validate(self, value):
        if not isinstance(value, (bytes, bytearray)):
            raise TypeError("Bytes or bytearray expected")

    @classmethod
    def from_bytes(cls, bytes):
        raise NotImplementedError


class TimeParameter(_Parameter):
    def __init__(self, init_value=None):
        super().__init__(format_code=0, init_value=init_value)

    @property
    def format(self):
        return f"{len(self.value)}s"

    def _validate(self, value):
        if not isinstance(value, CucTime):
            raise TypeError("CucTime expected")

    @classmethod
    def from_bytes(cls, bytes):
        raise NotImplementedError


class AbsoluteTimeParameter(TimeParameter):
    _type_code = PacketFieldType.AbsoluteTime


class RelativeTimeParameter(TimeParameter):
    _type_code = PacketFieldType.RelativeTime


class PacketParameter(_Parameter):
    _type_code = PacketFieldType.Packet

    def _validate(self, value):
        if not isinstance(value, PusTcPacket):
            raise TypeError("PusTcPacket expected")

    @property
    def format(self):
        return f"{len(self.value)}s"

    @classmethod
    def from_bytes(cls, bytes):
        raise NotImplementedError
