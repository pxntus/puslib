"""Parameter types to be used for parametric system in PUS.

Relevant for the following PUS services:

- housekeeping service
- event reporting service
- parameter management service
"""

import struct
from enum import IntEnum

from puslib.time import CucTime
from puslib.packet import PusTcPacket


class PacketFieldType(IntEnum):
    BOOLEAN = 1
    ENUMERATED = 2
    UINT = 3
    INT = 4
    REAL = 5
    BIT_STRING = 6
    OCTET_STRING = 7
    STRING = 8
    ABSOLUTE_TIME = 9
    RELATIVE_TIME = 10
    DEDUCTED = 11
    PACKET = 12


class Parameter:
    """Represent a PUS parameter.

    Base class for concrete child classes.
    """
    _type_code = None

    def __init__(self, format_code: PacketFieldType, init_value=None):
        self._format_code = format_code
        if init_value:
            self._validate(init_value)
        self._value = init_value
        self._events = []

    def __bytes__(self):
        return struct.pack(self.format, self.value)

    def __len__(self):
        return struct.calcsize(self.format)

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
    def ptc(self) -> int:
        """Return the packet field type code of the parameter.

        Returns:
            packet field type code (PTC)
        """
        return self._type_code

    @property
    def pfc(self) -> int:
        """Return the packet field format code of the parameter.

        Returns:
            packet field format code (PFC)
        """
        return self._format_code

    @property
    def format(self) -> str:
        """Return the struct format string of the parameter.

        This is used to effectively combine multiple parameters in one pack operation.

        Returns:
            struct format string
        """
        raise NotImplementedError

    def subscribe(self, event_handler):
        """Subscribe to the parameter.

        Arguments:
            event_handler -- event handler to receive updates
        """
        self._events.append(event_handler)

    def _validate(self, value):
        raise NotImplementedError


class BoolParameter(Parameter):
    _type_code = PacketFieldType.BOOLEAN
    _fmt = '>?'
    _struct = struct.Struct(_fmt)

    def __init__(self, init_value=False):
        super().__init__(format_code=8, init_value=init_value)

    def __len__(self):
        return 1

    @property
    def format(self):
        return self._fmt

    def _validate(self, value):
        if not isinstance(value, bool):
            raise TypeError("Boolean expected")

    @classmethod
    def from_bytes(cls, buffer):
        return cls._struct.unpack(buffer)[0]


class EnumParameter(Parameter):
    _type_code = PacketFieldType.ENUMERATED

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
        if not 0 <= value <= (2 ** self._format_code - 1):
            raise ValueError

    @classmethod
    def from_bytes(cls, buffer, bitsize):
        value_size = bitsize // 8 + (1 if bitsize % 8 != 0 else 0)
        return int.from_bytes(buffer[:value_size], byteorder='big')


class NumericParameter(Parameter):
    _value_size = 0
    _fmt = None

    def __len__(self):
        return self._value_size

    @property
    def format(self):
        return self._fmt

    def _validate(self, value):
        raise NotImplementedError


class _IntegerParameter(NumericParameter):
    _signed = None

    def __bytes__(self):
        return self.value.to_bytes(self._value_size, byteorder='big', signed=self._signed)

    @classmethod
    def from_bytes(cls, buffer):
        return int.from_bytes(buffer[:cls._value_size], byteorder='big', signed=cls._signed)

    def _validate(self, value):
        raise NotImplementedError


class _UnsignedIntegerParameter(_IntegerParameter):
    _type_code = PacketFieldType.UINT
    _signed = False

    def _validate(self, value):
        if not isinstance(value, int):
            raise TypeError("Integer expected")
        if not 0 <= value <= (2 ** (self._value_size * 8) - 1):
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
    _type_code = PacketFieldType.INT
    _signed = True

    def _validate(self, value):
        if not isinstance(value, int):
            raise TypeError("Integer expected")
        if not (-2 ** (len(self) * 8 - 1)) <= value <= (2 ** (self._value_size * 8 - 1) - 1):
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
    _type_code = PacketFieldType.REAL
    _fmt = None
    _struct = None

    def _validate(self, value):
        if not isinstance(value, float):
            raise TypeError("Float expected")

    @classmethod
    def from_bytes(cls, buffer):
        return cls._struct.unpack(buffer)[0]


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


class ArrayParameter(Parameter):
    def _validate(self, value):
        raise NotImplementedError


class OctetStringParameter(ArrayParameter):
    _type_code = PacketFieldType.OCTET_STRING

    def __init__(self, init_value=None):
        super().__init__(format_code=0, init_value=init_value)

    def __len__(self):
        return len(self.value)

    @property
    def format(self, length_type):  # pylint: disable=arguments-differ
        return f"{length_type.format + len(self.value)}s"

    def _validate(self, value):
        if not isinstance(value, (bytes, bytearray)):
            raise TypeError("Bytes or bytearray expected")

    @classmethod
    def from_bytes(cls, buffer):
        raise NotImplementedError


class TimeParameter(Parameter):
    def __init__(self, init_value=None):
        super().__init__(format_code=0, init_value=init_value)

    @property
    def format(self):
        return f"{len(self.value)}s"

    def _validate(self, value):
        if not isinstance(value, CucTime):
            raise TypeError("CucTime expected")

    @classmethod
    def from_bytes(cls, buffer):
        raise NotImplementedError


class AbsoluteTimeParameter(TimeParameter):
    _type_code = PacketFieldType.ABSOLUTE_TIME

    @classmethod
    def from_bytes(cls, buffer):
        raise NotImplementedError


class RelativeTimeParameter(TimeParameter):
    _type_code = PacketFieldType.RELATIVE_TIME

    @classmethod
    def from_bytes(cls, buffer):
        raise NotImplementedError


class PacketParameter(Parameter):
    _type_code = PacketFieldType.PACKET

    def _validate(self, value):
        if not isinstance(value, PusTcPacket):
            raise TypeError("PusTcPacket expected")

    @property
    def format(self):
        return f"{len(self.value)}s"

    @classmethod
    def from_bytes(cls, buffer):
        raise NotImplementedError
